"""
Data Augmentation Plugin
Generate synthetic training data and augment existing datasets
"""

from typing import Dict, Any, Optional, List
import random


class DataAugmentationPlugin:
    """Plugin for data augmentation"""

    name = "data_augmentation"
    version = "1.0.0"
    description = "Generate and augment training data"
    author = "Windows AI Team"

    def __init__(self):
        self.augmented_datasets = {}
        self._initialized = False

    def initialize(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Initialize the Data Augmentation plugin"""
        try:
            self._initialized = True
            return True
        except Exception as e:
            print(f"Error initializing Data Augmentation plugin: {e}")
            return False

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Data Augmentation action"""
        if not self._initialized:
            return {"success": False, "error": "Plugin not initialized"}

        try:
            if action == "text_augment":
                return self._text_augment(params)
            elif action == "back_translation":
                return self._back_translation(params)
            elif action == "paraphrase":
                return self._paraphrase(params)
            elif action == "synonym_replacement":
                return self._synonym_replacement(params)
            elif action == "mixup":
                return self._mixup(params)
            elif action == "generate_synthetic":
                return self._generate_synthetic(params)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _text_augment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """General text augmentation"""
        text = params.get("text", "")
        techniques = params.get("techniques", ["synonym", "insertion", "swap"])
        num_augmentations = params.get("num_augmentations", 3)

        augmented_texts = [text]  # Include original

        for _ in range(num_augmentations):
            aug_text = text

            for technique in techniques:
                if technique == "synonym":
                    aug_text = self._apply_synonym_replacement(aug_text)
                elif technique == "insertion":
                    aug_text = self._apply_random_insertion(aug_text)
                elif technique == "swap":
                    aug_text = self._apply_random_swap(aug_text)
                elif technique == "deletion":
                    aug_text = self._apply_random_deletion(aug_text)

            augmented_texts.append(aug_text)

        return {
            "success": True,
            "original": text,
            "augmented": augmented_texts,
            "count": len(augmented_texts)
        }

    def _apply_synonym_replacement(self, text: str) -> str:
        """Replace words with synonyms"""
        words = text.split()
        if not words:
            return text

        # Simulate synonym replacement
        idx = random.randint(0, len(words) - 1)
        words[idx] = f"[SYN:{words[idx]}]"  # Placeholder for synonym

        return " ".join(words)

    def _apply_random_insertion(self, text: str) -> str:
        """Insert random synonym of random word"""
        words = text.split()
        if not words:
            return text

        idx = random.randint(0, len(words))
        words.insert(idx, "[INSERTED_WORD]")

        return " ".join(words)

    def _apply_random_swap(self, text: str) -> str:
        """Swap two random words"""
        words = text.split()
        if len(words) < 2:
            return text

        idx1, idx2 = random.sample(range(len(words)), 2)
        words[idx1], words[idx2] = words[idx2], words[idx1]

        return " ".join(words)

    def _apply_random_deletion(self, text: str) -> str:
        """Randomly delete words"""
        words = text.split()
        if not words:
            return text

        # Keep at least 50% of words
        keep_prob = 0.7
        words = [w for w in words if random.random() < keep_prob or len(words) < 3]

        return " ".join(words) if words else text

    def _back_translation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Back translation for paraphrasing"""
        text = params.get("text", "")
        intermediate_languages = params.get("languages", ["fr", "de"])

        # Simulate back translation
        augmented = [text]

        for lang in intermediate_languages:
            # Simulate translation to lang and back
            back_translated = f"[BACK_TRANSLATED via {lang}]: {text}"
            augmented.append(back_translated)

        return {
            "success": True,
            "original": text,
            "augmented": augmented,
            "languages_used": intermediate_languages
        }

    def _paraphrase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate paraphrases"""
        text = params.get("text", "")
        num_paraphrases = params.get("num_paraphrases", 3)

        # Simulate paraphrasing
        paraphrases = []

        for i in range(num_paraphrases):
            # In production, would use paraphrasing model
            paraphrase = f"Paraphrase {i+1}: {text}"
            paraphrases.append(paraphrase)

        return {
            "success": True,
            "original": text,
            "paraphrases": paraphrases,
            "count": len(paraphrases)
        }

    def _synonym_replacement(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Replace words with synonyms"""
        text = params.get("text", "")
        num_replacements = params.get("num_replacements", 2)

        words = text.split()
        if len(words) < num_replacements:
            num_replacements = len(words)

        # Select random words to replace
        indices = random.sample(range(len(words)), num_replacements)

        augmented_texts = []

        for _ in range(3):  # Generate 3 variations
            new_words = words.copy()
            for idx in indices:
                new_words[idx] = f"[SYN:{words[idx]}]"

            augmented_texts.append(" ".join(new_words))

        return {
            "success": True,
            "original": text,
            "augmented": augmented_texts,
            "replacements": num_replacements
        }

    def _mixup(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mixup augmentation for text pairs"""
        text1 = params.get("text1", "")
        text2 = params.get("text2", "")
        label1 = params.get("label1", 0)
        label2 = params.get("label2", 1)
        alpha = params.get("alpha", 0.2)  # Mixup parameter

        # Simulate mixup
        lambda_val = random.betavariate(alpha, alpha)

        # In production, would actually mix representations
        # Here we simulate by combining texts
        mixed_text = f"MixUp({lambda_val:.2f}): [{text1}] + [{text2}]"
        mixed_label = lambda_val * label1 + (1 - lambda_val) * label2

        return {
            "success": True,
            "original_texts": [text1, text2],
            "mixed_text": mixed_text,
            "mixed_label": mixed_label,
            "lambda": lambda_val
        }

    def _generate_synthetic(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate synthetic training examples"""
        template = params.get("template", "")
        num_examples = params.get("num_examples", 10)
        variables = params.get("variables", {})

        synthetic_examples = []

        for i in range(num_examples):
            example = template

            # Fill in variables
            for var_name, var_values in variables.items():
                if var_values:
                    value = random.choice(var_values)
                    example = example.replace(f"{{{var_name}}}", str(value))

            synthetic_examples.append({
                "text": example,
                "synthetic": True,
                "template_id": hash(template) % 10000
            })

        return {
            "success": True,
            "synthetic_examples": synthetic_examples,
            "count": len(synthetic_examples),
            "template": template
        }

    def shutdown(self) -> bool:
        """Cleanup plugin resources"""
        self._initialized = False
        self.augmented_datasets = {}
        return True
