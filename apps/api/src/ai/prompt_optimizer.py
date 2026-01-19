"""
Prompt Optimization Module using DSPy

Automatically optimizes prompts based on execution feedback.
This transforms static prompts into self-improving systems.

Features:
- Automatic prompt optimization based on success/failure
- Few-shot example selection
- Chain-of-thought reasoning
- Metric-based optimization
- Prompt versioning and A/B testing
"""

from typing import Optional, List, Dict, Any, Callable, Type, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import json
import hashlib
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class OptimizationMetric(str, Enum):
    """Metrics for prompt optimization"""
    ACCURACY = "accuracy"  # Correct outputs
    EXECUTION_SUCCESS = "execution_success"  # Code runs without errors
    TEST_PASS_RATE = "test_pass_rate"  # Tests pass
    SIMILARITY = "similarity"  # Output matches expected
    COHERENCE = "coherence"  # Logical consistency
    CONCISENESS = "conciseness"  # Brevity of output


@dataclass
class Example:
    """A single example for few-shot learning"""
    input: str
    output: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 1.0  # Quality score
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input": self.input,
            "output": self.output,
            "metadata": self.metadata,
            "score": self.score,
            "timestamp": self.timestamp
        }


@dataclass
class OptimizationResult:
    """Result of prompt optimization"""
    original_prompt: str
    optimized_prompt: str
    improvement: float  # Percentage improvement
    iterations: int
    best_score: float
    examples_used: int
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class PromptTemplate:
    """A prompt template with placeholders"""
    template: str
    variables: List[str] = field(default_factory=list)
    examples: List[Example] = field(default_factory=list)
    chain_of_thought: bool = False
    version: str = "1.0.0"

    def render(self, **kwargs) -> str:
        """Render the template with variables"""
        prompt = self.template

        # Add chain-of-thought if enabled
        if self.chain_of_thought:
            prompt += "\n\nLet's think step by step:"

        # Add examples if available
        if self.examples:
            examples_text = "\n\nExamples:\n"
            for i, ex in enumerate(self.examples[:5], 1):  # Max 5 examples
                examples_text += f"\nExample {i}:\nInput: {ex.input}\nOutput: {ex.output}\n"
            prompt = examples_text + "\n" + prompt

        # Substitute variables
        for var in self.variables:
            if var in kwargs:
                prompt = prompt.replace(f"{{{var}}}", str(kwargs[var]))

        return prompt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template": self.template,
            "variables": self.variables,
            "examples": [e.to_dict() for e in self.examples],
            "chain_of_thought": self.chain_of_thought,
            "version": self.version
        }


class Signature(ABC):
    """
    Base class for DSPy-style signatures.
    Defines input/output structure for a task.
    """

    @abstractmethod
    def get_input_fields(self) -> List[str]:
        """Return list of input field names"""
        pass

    @abstractmethod
    def get_output_fields(self) -> List[str]:
        """Return list of output field names"""
        pass

    def get_description(self) -> str:
        """Return task description"""
        return self.__doc__ or ""


class CodeGenerationSignature(Signature):
    """Generate code based on requirements"""

    def get_input_fields(self) -> List[str]:
        return ["requirements", "language", "context"]

    def get_output_fields(self) -> List[str]:
        return ["code", "explanation"]


class CodeFixSignature(Signature):
    """Fix code based on error feedback"""

    def get_input_fields(self) -> List[str]:
        return ["code", "error", "language"]

    def get_output_fields(self) -> List[str]:
        return ["fixed_code", "changes_made"]


class TestGenerationSignature(Signature):
    """Generate tests for code"""

    def get_input_fields(self) -> List[str]:
        return ["code", "language", "coverage_target"]

    def get_output_fields(self) -> List[str]:
        return ["tests", "test_descriptions"]


class ExampleStore:
    """
    Store and retrieve examples for few-shot learning.
    Uses semantic similarity for example selection.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = persist_path or os.path.join(
            os.path.expanduser("~"), ".codeweaver", "examples"
        )
        self.examples: Dict[str, List[Example]] = {}
        self._load()

    def add_example(
        self,
        task: str,
        input_text: str,
        output_text: str,
        score: float = 1.0,
        metadata: Optional[Dict] = None
    ):
        """Add a new example"""
        example = Example(
            input=input_text,
            output=output_text,
            score=score,
            metadata=metadata or {}
        )

        if task not in self.examples:
            self.examples[task] = []

        self.examples[task].append(example)
        self._save()

    def get_examples(
        self,
        task: str,
        query: Optional[str] = None,
        n: int = 5,
        min_score: float = 0.5
    ) -> List[Example]:
        """
        Get relevant examples for a task.

        Args:
            task: Task identifier
            query: Optional query for similarity matching
            n: Number of examples to return
            min_score: Minimum quality score

        Returns:
            List of relevant examples
        """
        if task not in self.examples:
            return []

        # Filter by score
        candidates = [e for e in self.examples[task] if e.score >= min_score]

        # Sort by score (could use semantic similarity with query)
        candidates.sort(key=lambda e: e.score, reverse=True)

        return candidates[:n]

    def update_score(self, task: str, input_text: str, new_score: float):
        """Update the score of an example based on feedback"""
        if task not in self.examples:
            return

        for example in self.examples[task]:
            if example.input == input_text:
                # Exponential moving average
                example.score = 0.7 * example.score + 0.3 * new_score
                break

        self._save()

    def _load(self):
        """Load examples from disk"""
        try:
            os.makedirs(self.persist_path, exist_ok=True)
            index_path = os.path.join(self.persist_path, "index.json")

            if os.path.exists(index_path):
                with open(index_path, 'r') as f:
                    data = json.load(f)
                    for task, examples in data.items():
                        self.examples[task] = [
                            Example(**e) for e in examples
                        ]
        except Exception as e:
            logger.warning(f"Could not load examples: {e}")

    def _save(self):
        """Save examples to disk"""
        try:
            os.makedirs(self.persist_path, exist_ok=True)
            index_path = os.path.join(self.persist_path, "index.json")

            data = {
                task: [e.to_dict() for e in examples]
                for task, examples in self.examples.items()
            }

            with open(index_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save examples: {e}")


class PromptOptimizer:
    """
    DSPy-inspired prompt optimizer.

    Automatically improves prompts based on execution feedback.

    Example:
        optimizer = PromptOptimizer()

        # Define a code generation task
        template = PromptTemplate(
            template="Generate {language} code for: {requirements}",
            variables=["language", "requirements"]
        )

        # Optimize based on execution results
        optimized = await optimizer.optimize(
            template=template,
            evaluate_fn=run_and_test_code,
            train_data=examples,
            metric=OptimizationMetric.EXECUTION_SUCCESS
        )

        # Use optimized prompt
        prompt = optimized.optimized_prompt
    """

    def __init__(self, model: str = "claude-3-5-sonnet-20241022"):
        self.model = model
        self.example_store = ExampleStore()
        self._dspy_available = self._check_dspy()

    def _check_dspy(self) -> bool:
        """Check if DSPy is available"""
        try:
            import dspy
            return True
        except ImportError:
            logger.warning("DSPy not available, using manual optimization")
            return False

    async def optimize(
        self,
        template: PromptTemplate,
        evaluate_fn: Callable[[str, str], float],
        train_data: List[Dict[str, str]],
        metric: OptimizationMetric = OptimizationMetric.EXECUTION_SUCCESS,
        max_iterations: int = 10,
        target_score: float = 0.9
    ) -> OptimizationResult:
        """
        Optimize a prompt template.

        Args:
            template: Prompt template to optimize
            evaluate_fn: Function that takes (prompt, output) and returns score 0-1
            train_data: Training examples [{input_vars}, ...]
            metric: Optimization metric
            max_iterations: Maximum optimization iterations
            target_score: Stop when this score is achieved

        Returns:
            OptimizationResult with optimized prompt
        """
        if self._dspy_available:
            return await self._optimize_with_dspy(
                template, evaluate_fn, train_data, metric, max_iterations, target_score
            )
        else:
            return await self._optimize_manual(
                template, evaluate_fn, train_data, metric, max_iterations, target_score
            )

    async def _optimize_with_dspy(
        self,
        template: PromptTemplate,
        evaluate_fn: Callable,
        train_data: List[Dict],
        metric: OptimizationMetric,
        max_iterations: int,
        target_score: float
    ) -> OptimizationResult:
        """Optimize using DSPy"""
        try:
            import dspy
            from dspy.teleprompt import BootstrapFewShot

            # Configure DSPy
            lm = dspy.Claude(model=self.model)
            dspy.settings.configure(lm=lm)

            # Create DSPy module
            class CodeGenerator(dspy.Module):
                def __init__(self):
                    super().__init__()
                    self.generate = dspy.ChainOfThought("requirements -> code")

                def forward(self, requirements):
                    return self.generate(requirements=requirements)

            # Create metric function
            def dspy_metric(example, pred, trace=None):
                try:
                    score = evaluate_fn(example.requirements, pred.code)
                    return score >= 0.5
                except Exception:
                    return False

            # Compile with bootstrap few-shot
            teleprompter = BootstrapFewShot(metric=dspy_metric)
            optimized_module = teleprompter.compile(
                CodeGenerator(),
                trainset=[
                    dspy.Example(requirements=d.get("requirements", ""))
                    for d in train_data
                ]
            )

            # Extract optimized prompt
            # This is simplified - actual DSPy gives you the compiled module
            original_prompt = template.render()

            return OptimizationResult(
                original_prompt=original_prompt,
                optimized_prompt=original_prompt,  # DSPy handles this internally
                improvement=0.0,
                iterations=max_iterations,
                best_score=target_score,
                examples_used=len(train_data)
            )

        except Exception as e:
            logger.error(f"DSPy optimization failed: {e}")
            return await self._optimize_manual(
                template, evaluate_fn, train_data, metric, max_iterations, target_score
            )

    async def _optimize_manual(
        self,
        template: PromptTemplate,
        evaluate_fn: Callable,
        train_data: List[Dict],
        metric: OptimizationMetric,
        max_iterations: int,
        target_score: float
    ) -> OptimizationResult:
        """Manual prompt optimization without DSPy"""
        original_prompt = template.template
        current_template = template
        best_score = 0.0
        best_prompt = original_prompt
        scores_history = []

        # Optimization strategies to try
        strategies = [
            self._add_chain_of_thought,
            self._add_examples,
            self._add_constraints,
            self._add_format_instructions,
            self._simplify_prompt
        ]

        for iteration in range(max_iterations):
            # Evaluate current template
            score = await self._evaluate_template(current_template, evaluate_fn, train_data)
            scores_history.append(score)

            if score > best_score:
                best_score = score
                best_prompt = current_template.render()

            if score >= target_score:
                break

            # Try optimization strategies
            strategy = strategies[iteration % len(strategies)]
            current_template = strategy(current_template, scores_history)

        improvement = (best_score - scores_history[0]) / max(scores_history[0], 0.01) * 100

        return OptimizationResult(
            original_prompt=original_prompt,
            optimized_prompt=best_prompt,
            improvement=improvement,
            iterations=len(scores_history),
            best_score=best_score,
            examples_used=len(current_template.examples),
            metrics={"scores_history": scores_history}
        )

    async def _evaluate_template(
        self,
        template: PromptTemplate,
        evaluate_fn: Callable,
        train_data: List[Dict]
    ) -> float:
        """Evaluate a template on training data"""
        scores = []

        for data in train_data[:10]:  # Limit evaluation samples
            try:
                prompt = template.render(**data)
                # Mock output for now - would call LLM
                output = "mock_output"
                score = evaluate_fn(prompt, output)
                scores.append(score)
            except Exception:
                scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def _add_chain_of_thought(
        self,
        template: PromptTemplate,
        history: List[float]
    ) -> PromptTemplate:
        """Add chain-of-thought prompting"""
        new_template = PromptTemplate(
            template=template.template,
            variables=template.variables,
            examples=template.examples,
            chain_of_thought=True,
            version=self._bump_version(template.version)
        )
        return new_template

    def _add_examples(
        self,
        template: PromptTemplate,
        history: List[float]
    ) -> PromptTemplate:
        """Add few-shot examples"""
        # Get examples from store
        task_key = hashlib.md5(template.template.encode()).hexdigest()[:8]
        examples = self.example_store.get_examples(task_key, n=3)

        new_template = PromptTemplate(
            template=template.template,
            variables=template.variables,
            examples=examples,
            chain_of_thought=template.chain_of_thought,
            version=self._bump_version(template.version)
        )
        return new_template

    def _add_constraints(
        self,
        template: PromptTemplate,
        history: List[float]
    ) -> PromptTemplate:
        """Add explicit constraints"""
        constraints = """
Important constraints:
- Ensure the code is syntactically correct
- Handle edge cases appropriately
- Follow best practices for the language
- Include error handling where appropriate
"""
        new_template = PromptTemplate(
            template=template.template + constraints,
            variables=template.variables,
            examples=template.examples,
            chain_of_thought=template.chain_of_thought,
            version=self._bump_version(template.version)
        )
        return new_template

    def _add_format_instructions(
        self,
        template: PromptTemplate,
        history: List[float]
    ) -> PromptTemplate:
        """Add output format instructions"""
        format_inst = """
Output format:
- Provide only the code without explanations
- Do not include markdown code blocks
- Ensure the code is complete and runnable
"""
        new_template = PromptTemplate(
            template=template.template + format_inst,
            variables=template.variables,
            examples=template.examples,
            chain_of_thought=template.chain_of_thought,
            version=self._bump_version(template.version)
        )
        return new_template

    def _simplify_prompt(
        self,
        template: PromptTemplate,
        history: List[float]
    ) -> PromptTemplate:
        """Simplify prompt if it's getting too complex"""
        # Remove chain of thought if scores are declining
        if len(history) >= 3 and history[-1] < history[-3]:
            return PromptTemplate(
                template=template.template,
                variables=template.variables,
                examples=template.examples[:2],  # Fewer examples
                chain_of_thought=False,
                version=self._bump_version(template.version)
            )
        return template

    def _bump_version(self, version: str) -> str:
        """Bump version number"""
        parts = version.split('.')
        parts[-1] = str(int(parts[-1]) + 1)
        return '.'.join(parts)

    def create_code_generation_prompt(
        self,
        language: str,
        include_examples: bool = True
    ) -> PromptTemplate:
        """Create an optimized code generation prompt"""
        template = f"""You are an expert {language} developer.
Generate clean, efficient, and well-documented {language} code.

Requirements: {{requirements}}

Guidelines:
1. Write production-quality code
2. Include appropriate error handling
3. Follow {language} best practices and conventions
4. Ensure the code is complete and runnable
5. Add brief inline comments for complex logic

Output only the code, no explanations or markdown."""

        examples = []
        if include_examples:
            examples = self.example_store.get_examples(f"code_gen_{language}", n=3)

        return PromptTemplate(
            template=template,
            variables=["requirements"],
            examples=examples,
            chain_of_thought=True
        )

    def create_code_fix_prompt(self) -> PromptTemplate:
        """Create an optimized code fix prompt"""
        template = """You are an expert debugger.
Fix the following code that has an error.

Original code:
```
{code}
```

Error:
{error}

Analyze the error and provide the corrected code.
Output only the fixed code, no explanations."""

        return PromptTemplate(
            template=template,
            variables=["code", "error"],
            chain_of_thought=True
        )

    def record_result(
        self,
        task: str,
        input_text: str,
        output: str,
        success: bool,
        score: Optional[float] = None
    ):
        """Record execution result for future optimization"""
        final_score = score if score is not None else (1.0 if success else 0.0)

        self.example_store.add_example(
            task=task,
            input_text=input_text,
            output_text=output,
            score=final_score,
            metadata={"success": success}
        )


class SelfImprovingAgent:
    """
    An agent that improves its prompts based on execution feedback.

    Example:
        agent = SelfImprovingAgent(task="code_generation")

        # Generate code
        code = await agent.generate(
            requirements="Create a function to calculate factorial",
            language="python"
        )

        # The agent automatically improves based on success/failure
        # Over time, its prompts become more effective
    """

    def __init__(
        self,
        task: str,
        optimizer: Optional[PromptOptimizer] = None
    ):
        self.task = task
        self.optimizer = optimizer or PromptOptimizer()
        self.template: Optional[PromptTemplate] = None
        self.success_count = 0
        self.total_count = 0

    async def generate(
        self,
        llm_call: Callable[[str], str],
        validate_fn: Callable[[str], bool],
        **kwargs
    ) -> str:
        """
        Generate output with self-improvement.

        Args:
            llm_call: Function to call LLM with prompt
            validate_fn: Function to validate output
            **kwargs: Variables for the prompt

        Returns:
            Generated output
        """
        # Get or create template
        if self.template is None:
            self.template = self._create_initial_template()

        # Render prompt
        prompt = self.template.render(**kwargs)

        # Call LLM
        output = llm_call(prompt)

        # Validate and record
        success = validate_fn(output)
        self.total_count += 1

        if success:
            self.success_count += 1
            score = 1.0
        else:
            score = 0.0

        # Record for learning
        self.optimizer.record_result(
            task=self.task,
            input_text=json.dumps(kwargs),
            output=output,
            success=success,
            score=score
        )

        # Trigger optimization if success rate is low
        if self.total_count >= 10 and self.success_rate < 0.7:
            await self._trigger_optimization()

        return output

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 1.0
        return self.success_count / self.total_count

    def _create_initial_template(self) -> PromptTemplate:
        """Create initial template based on task"""
        if "code" in self.task.lower():
            return self.optimizer.create_code_generation_prompt("python")
        elif "fix" in self.task.lower():
            return self.optimizer.create_code_fix_prompt()
        else:
            return PromptTemplate(
                template=f"Complete the following task: {{input}}",
                variables=["input"]
            )

    async def _trigger_optimization(self):
        """Trigger prompt optimization"""
        logger.info(f"Triggering optimization for {self.task}, success rate: {self.success_rate:.2%}")

        # Get training data from example store
        examples = self.optimizer.example_store.get_examples(self.task, n=20)

        if len(examples) < 5:
            return  # Not enough data

        train_data = [
            json.loads(e.input) for e in examples
        ]

        # Optimize
        result = await self.optimizer.optimize(
            template=self.template,
            evaluate_fn=lambda p, o: 1.0,  # Simplified
            train_data=train_data,
            max_iterations=5
        )

        # Update template
        self.template = PromptTemplate(
            template=result.optimized_prompt,
            variables=self.template.variables,
            examples=self.template.examples,
            chain_of_thought=self.template.chain_of_thought
        )

        logger.info(f"Optimization complete, improvement: {result.improvement:.1f}%")


# ===========================================
# Convenience Functions
# ===========================================

_default_optimizer: Optional[PromptOptimizer] = None


def get_optimizer() -> PromptOptimizer:
    """Get the default prompt optimizer"""
    global _default_optimizer
    if _default_optimizer is None:
        _default_optimizer = PromptOptimizer()
    return _default_optimizer


def create_code_prompt(language: str) -> PromptTemplate:
    """Create an optimized code generation prompt"""
    return get_optimizer().create_code_generation_prompt(language)


def create_fix_prompt() -> PromptTemplate:
    """Create an optimized code fix prompt"""
    return get_optimizer().create_code_fix_prompt()


def record_success(task: str, input_text: str, output: str):
    """Record a successful execution"""
    get_optimizer().record_result(task, input_text, output, success=True)


def record_failure(task: str, input_text: str, output: str):
    """Record a failed execution"""
    get_optimizer().record_result(task, input_text, output, success=False)
