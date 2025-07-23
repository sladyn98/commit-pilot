import os
from typing import Optional

from config import Config
from core.analyzer import DiffSummary, build_prompt
import tiktoken

class OpenAIProvider:
    
    def __init__(self, config: Config):
        self.config = config
        self.api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self._client: Optional[object] = None
        self._encoder: Optional[object] = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError as e:
                raise ImportError("OpenAI package not installed. Run: pip install openai") from e
            
            self._client = OpenAI(api_key=self.api_key)
        return self._client
    
    @property
    def encoder(self):
        if self._encoder is None:            
            self._encoder = tiktoken.encoding_for_model(self.config.openai_model)
        return self._encoder
    
    def count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))
    
    def _trim_files_for_token_limit(self, summary: DiffSummary) -> DiffSummary:
        prompt = build_prompt(summary)
        
        if self.count_tokens(prompt) <= self.config.max_prompt_tokens:
            return summary
        
        
        sorted_files = sorted(
            summary.files, 
            key=lambda f: f.added + f.removed, 
            reverse=True
        )
        
        
        left, right = 1, len(sorted_files)
        best_files = sorted_files[:1]  
        
        while left <= right:
            mid = (left + right) // 2
            test_files = sorted_files[:mid]
            
            test_summary = DiffSummary(
                files=test_files,
                total_added=sum(f.added for f in test_files),
                total_removed=sum(f.removed for f in test_files),
                change_type=summary.change_type
            )
            
            test_prompt = build_prompt(test_summary)
            
            if self.count_tokens(test_prompt) <= self.config.max_prompt_tokens:
                best_files = test_files
                left = mid + 1
            else:
                right = mid - 1
        
        
        return DiffSummary(
            files=best_files,
            total_added=sum(f.added for f in best_files),
            total_removed=sum(f.removed for f in best_files),
            change_type=summary.change_type
        )
    
    def generate_commit(self, summary: DiffSummary) -> str:
        
        trimmed_summary = self._trim_files_for_token_limit(summary)
        
        
        prompt = build_prompt(trimmed_summary)
        
        
        token_count = self.count_tokens(prompt)
        if token_count > self.config.max_prompt_tokens:
            raise RuntimeError(f"Prompt still too long: {token_count} tokens > {self.config.max_prompt_tokens}")
        
        # Print the prompt before submitting to LLM
        print("\n" + "="*50)
        print("PROMPT BEING SENT TO LLM:")
        print("="*50)
        print(prompt)
        print("="*50 + "\n")
        os._exit(1)
        
        try:
            response = self.client.chat.completions.create(
                model=self.config.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a git commit message generator. Generate concise, "
                        "clear commit messages following Conventional Commits specification. "
                        "Return only the commit message, no explanations or markdown."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300,  
            )
            
            message = response.choices[0].message.content.strip()
            
            if not message:
                raise ValueError("Empty response from OpenAI")
            
            
            message = self._clean_commit_message(message)
            
            return message
            
        except Exception as e:
            raise RuntimeError(f"Failed to generate commit message: {str(e)}") from e
    
    def _clean_commit_message(self, message: str) -> str:
        lines = message.split('\n')
        
        
        lines = [line.strip('`').strip() for line in lines]
        
        
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        
        if not lines:
            return "chore: update files"
        
        
        if len(lines[0]) > 72:
            lines[0] = lines[0][:69] + "..."
        
        
        if len(lines) > 4:  
            lines = lines[:4]
        
        return '\n'.join(lines)