"""
Unified LLM API wrapper supporting multiple model providers and automatic fallbacks.
"""

from enum import Enum
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    GEMINI = "gemini"
    GROQ = "groq"
    OPENROUTER = "openrouter"
    COHERE = "cohere"
    OPENAI = "openai"


# Default models for free tier
DEFAULT_MODELS = {
    LLMProvider.GEMINI: "gemini-2.5-flash",
    LLMProvider.GROQ: "llama-3.3-70b-versatile",
    LLMProvider.OPENROUTER: "meta-llama/llama-3-8b-instruct:free",
    LLMProvider.COHERE: "command-r-plus",
    LLMProvider.OPENAI: "gpt-4o-mini"
}


class LLMWrapper:
    """
    A unified wrapper for LLM APIs supporting free-tier options and automatic fallbacks.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> None:
        """
        Initialize the LLMWrapper.

        Args:
            provider: Primary LLM provider name.
            model: Model name override.
            api_key: API key override.
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key

        # Load API keys from environment
        self.keys = {
            LLMProvider.GEMINI: os.getenv("GEMINI_API_KEY"),
            LLMProvider.GROQ: os.getenv("GROQ_API_KEY"),
            LLMProvider.OPENROUTER: os.getenv("OPENROUTER_API_KEY"),
            LLMProvider.COHERE: os.getenv("COHERE_API_KEY"),
            LLMProvider.OPENAI: os.getenv("OPENAI_API_KEY")
        }

        # Override if specific key passed
        if api_key and provider:
            self.keys[provider] = api_key

        # If no provider specified, auto-detect based on available keys
        if not self.provider:
            for key_prov in [
                LLMProvider.GEMINI,
                LLMProvider.GROQ,
                LLMProvider.OPENROUTER,
                LLMProvider.COHERE,
                LLMProvider.OPENAI
            ]:
                if self.keys[key_prov]:
                    self.provider = key_prov
                    break

            # Fallback if no keys found in env: default to gemini if it will be supplied later
            if not self.provider:
                self.provider = LLMProvider.GEMINI
                logger.warning("[NO_API_KEYS] Provider defaulted to gemini")

        if not self.model:
            self.model = DEFAULT_MODELS.get(self.provider, "gemini-2.5-flash")

        logger.info(f"[LLM_INIT] Provider: {self.provider} | Model: {self.model}")

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> str:
        """
        Generate response using the selected provider, with automatic fallback if configured.

        Args:
            prompt: Text prompt input.
            system_instruction: Optional developer instruction.
            temperature: Sampling temperature.
            max_tokens: Maximum output token count.

        Returns:
            The generated response string.
        """
        # Collect active providers we can try
        available_providers = []
        # Put the primary provider first
        if self.provider:
            available_providers.append((self.provider, self.model))

        # Add other providers for which we have keys as fallback options
        for p, k in self.keys.items():
            if k and p != self.provider:
                available_providers.append((p, DEFAULT_MODELS[p]))

        last_error = None
        for prov, mod in available_providers:
            key_val = self.keys[prov]
            if not key_val:
                continue

            try:
                logger.info(f"[GENERATION_ATTEMPT] Provider: {prov} | Model: {mod}")
                if prov == LLMProvider.GEMINI:
                    return self._generate_gemini(
                        prompt, mod,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                if prov == LLMProvider.GROQ:
                    return self._generate_groq(
                        prompt, mod,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                if prov == LLMProvider.OPENROUTER:
                    return self._generate_openrouter(
                        prompt, mod,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                if prov == LLMProvider.COHERE:
                    return self._generate_cohere(
                        prompt, mod,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                if prov == LLMProvider.OPENAI:
                    return self._generate_openai(
                        prompt, mod,
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
            except Exception as ex:
                logger.error(f"[GENERATION_ERROR] Provider: {prov} | Error: {ex}")
                last_error = ex

        # If all failed, or no key was available
        if last_error:
            raise last_error

        raise ValueError("No API keys found for any provider. Please set them in your environment or .env file.")

    def _generate_gemini(
        self,
        prompt: str,
        model: str,
        *,
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response via Gemini Client API."""
        api_key = self.keys.get(LLMProvider.GEMINI) or ""
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )
            return response.text or ""
        except ImportError:
            # Fall back to legacy google-generativeai package if installed
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=api_key)

            # Note: system_instruction goes in GenerativeModel constructor in legacy SDK
            model_obj = legacy_genai.GenerativeModel(
                model_name=model,
                system_instruction=system_instruction
            )
            response = model_obj.generate_content(
                prompt,
                generation_config={"temperature": temperature, "max_output_tokens": max_tokens}
            )
            return response.text or ""

    def _generate_groq(
        self,
        prompt: str,
        model: str,
        *,
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response via Groq API."""
        api_key = self.keys.get(LLMProvider.GROQ) or ""
        from groq import Groq
        client = Groq(api_key=api_key)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content or ""

    def _generate_openrouter(
        self,
        prompt: str,
        model: str,
        *,
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response via OpenRouter API."""
        api_key = self.keys.get(LLMProvider.OPENROUTER) or ""
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content or ""

    def _generate_cohere(
        self,
        prompt: str,
        model: str,
        *,
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response via Cohere API."""
        api_key = self.keys.get(LLMProvider.COHERE) or ""
        import cohere
        co = cohere.Client(api_key=api_key)

        response = co.chat(
            message=prompt,
            model=model,
            preamble=system_instruction,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.text or ""

    def _generate_openai(
        self,
        prompt: str,
        model: str,
        *,
        system_instruction: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> str:
        """Generate response via OpenAI API."""
        api_key = self.keys.get(LLMProvider.OPENAI) or ""
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return completion.choices[0].message.content or ""
