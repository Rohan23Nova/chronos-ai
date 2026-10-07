from typing import Any, Iterable, List, Optional, Set
from chronos.knowledge.rules import (
    Fact,
    Rule,
    get_default_rules,
    task_to_facts,
)


class RuleEngine:
    """
    Deterministic forward-chaining rule engine for symbolic reasoning.
    Derives new scheduling facts until a stable state (fixed point) is reached.
    """

    def __init__(self, rules: Optional[List[Rule]] = None):
        if rules is None:
            self.rules = get_default_rules()
        else:
            self.rules = list(rules)

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine's rule base."""
        self.rules.append(rule)

    def forward_chain(self, initial_facts: Iterable[Fact]) -> Set[Fact]:
        """
        Execute forward-chaining deduction starting from initial_facts.
        Repeatedly applies rules across all known entities until no new facts are derived.
        """
        facts: Set[Fact] = set(initial_facts)

        while True:
            new_facts: Set[Fact] = set()

            # Identify all distinct entities referenced in the current knowledge base
            entities = {f.entity_id for f in facts}

            # Sort entities deterministically to ensure reproducible rule firing
            sorted_entities = sorted(entities, key=lambda x: str(x))

            for rule in self.rules:
                for entity_id in sorted_entities:
                    if rule.matches(entity_id, facts):
                        derived_fact = rule.apply(entity_id)
                        if derived_fact not in facts:
                            new_facts.add(derived_fact)

            if not new_facts:
                break

            facts.update(new_facts)

        return facts

    def infer(self, task: Any, current_time: Optional[int] = None) -> Set[Fact]:
        """
        Derive all symbolic facts for a single task given the planning context.
        """
        initial_facts = task_to_facts(task, current_time)
        return self.forward_chain(initial_facts)

    def infer_all(self, tasks: Iterable[Any], current_time: Optional[int] = None) -> Set[Fact]:
        """
        Derive all symbolic facts across a collection of tasks.
        """
        initial_facts: Set[Fact] = set()
        for task in tasks:
            initial_facts.update(task_to_facts(task, current_time))
        return self.forward_chain(initial_facts)

    def get_derived_facts(self, initial_facts: Iterable[Fact]) -> Set[Fact]:
        """
        Return only the newly derived facts produced beyond the initial facts.
        """
        init_set = set(initial_facts)
        all_facts = self.forward_chain(init_set)
        return all_facts - init_set

    def query(
        self,
        facts: Iterable[Fact],
        predicate: Optional[str] = None,
        entity_id: Optional[Any] = None,
        value: Optional[Any] = None,
    ) -> List[Fact]:
        """
        Query facts matching specified criteria (None acts as wildcard).
        """
        results = []
        for f in facts:
            if predicate is not None and f.predicate != predicate:
                continue
            if entity_id is not None and f.entity_id != entity_id:
                continue
            if value is not None and f.value != value:
                continue
            results.append(f)
        return results

    def get_fact_value(
        self,
        facts: Iterable[Fact],
        predicate: str,
        entity_id: Any,
    ) -> Optional[Any]:
        """
        Get the value of a specific fact for an entity, or None if not found.
        """
        matches = self.query(facts, predicate=predicate, entity_id=entity_id)
        if matches:
            return matches[0].value
        return None


def get_default_engine() -> RuleEngine:
    """Factory creating a RuleEngine configured with standard Chronos domain rules."""
    return RuleEngine(get_default_rules())
