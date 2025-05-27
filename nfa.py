class NFA:
    def __init__(self, states, alphabet, transition, start, accept):
        self.states = states
        self.alphabet = alphabet
        self.transition = transition
        self.start = start
        self.accept = accept
    
    def epsilon_closure(self, states):
        stack = list(states)
        closure = set(states)
        while stack:
            state = stack.pop()
            for next_state in self.transition.get((state, ''), set()):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure
    
    def test(self, string):
        current = self.epsilon_closure({self.start})
        for symbol in string:
            next_states = set()
            for state in current:
                next_states |= self.transition.get((state, symbol), set())
            current = self.epsilon_closure(next_states)
        return bool(current & set(self.accept))

def regex_to_nfa(regex):
    """Mendukung: a, ab, a|b, a*, (a|b)*, +, dsb."""
    def new_state():
        new_state.counter += 1
        return f"S{new_state.counter}"
    new_state.counter = -1

    def to_postfix(regex):
        precedence = {'+': 3, '*': 4, '.': 2, '|': 1}
        output = []
        stack = []
        prev = None
        for c in regex:
            if c in {'(', '|', '*', '+'}:
                if c == '(':
                    stack.append(c)
                elif c in {'|'}:
                    while stack and stack[-1] != '(' and precedence[stack[-1]] >= precedence[c]:
                        output.append(stack.pop())
                    stack.append(c)
                elif c in {'*', '+'}:
                    output.append(c)
            elif c == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            else:
                if prev and (prev not in {'(', '|'} and prev != '.'):
                    while stack and stack[-1] != '(' and precedence[stack[-1]] >= precedence['.']:
                        output.append(stack.pop())
                    stack.append('.')
                output.append(c)
            prev = c
        while stack:
            output.append(stack.pop())
        return output

    def postfix_to_nfa(postfix):
        stack = []
        for token in postfix:
            if token == '*':
                nfa = stack.pop()
                start = new_state()
                end = new_state()
                transitions = nfa['transitions'].copy()
                transitions[(start, '')] = {nfa['start'], end}
                for a in nfa['accept']:
                    transitions.setdefault((a, ''), set()).update({nfa['start'], end})
                stack.append({
                    'start': start,
                    'accept': {end},
                    'states': nfa['states'] | {start, end},
                    'alphabet': nfa['alphabet'],
                    'transitions': transitions
                })
            elif token == '+':
                nfa = stack.pop()
                start_star = new_state()
                end_star = new_state()
                transitions_star = nfa['transitions'].copy()
                transitions_star[(start_star, '')] = {nfa['start'], end_star}
                for a in nfa['accept']:
                    transitions_star.setdefault((a, ''), set()).update({nfa['start'], end_star})
                nfa_star = {
                    'start': start_star,
                    'accept': {end_star},
                    'states': nfa['states'] | {start_star, end_star},
                    'alphabet': nfa['alphabet'],
                    'transitions': transitions_star
                }
                # Gabungkan nfa . nfa*
                transitions_concat = {**nfa['transitions']}
                for k, v in nfa_star['transitions'].items():
                    transitions_concat.setdefault(k, set()).update(v)
                for a in nfa['accept']:
                    transitions_concat.setdefault((a, ''), set()).add(nfa_star['start'])
                stack.append({
                    'start': nfa['start'],
                    'accept': nfa_star['accept'],
                    'states': nfa['states'] | nfa_star['states'],
                    'alphabet': nfa['alphabet'] | nfa_star['alphabet'],
                    'transitions': transitions_concat
                })
            elif token == '.':
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                transitions = {**nfa1['transitions']}
                for k, v in nfa2['transitions'].items():
                    transitions.setdefault(k, set()).update(v)
                for a in nfa1['accept']:
                    transitions.setdefault((a, ''), set()).add(nfa2['start'])
                stack.append({
                    'start': nfa1['start'],
                    'accept': nfa2['accept'],
                    'states': nfa1['states'] | nfa2['states'],
                    'alphabet': nfa1['alphabet'] | nfa2['alphabet'],
                    'transitions': transitions
                })
            elif token == '|':
                nfa2 = stack.pop()
                nfa1 = stack.pop()
                start = new_state()
                end = new_state()
                transitions = {**nfa1['transitions']}
                for k, v in nfa2['transitions'].items():
                    transitions.setdefault(k, set()).update(v)
                transitions[(start, '')] = {nfa1['start'], nfa2['start']}
                for a in nfa1['accept']:
                    transitions.setdefault((a, ''), set()).add(end)
                for a in nfa2['accept']:
                    transitions.setdefault((a, ''), set()).add(end)
                stack.append({
                    'start': start,
                    'accept': {end},
                    'states': nfa1['states'] | nfa2['states'] | {start, end},
                    'alphabet': nfa1['alphabet'] | nfa2['alphabet'],
                    'transitions': transitions
                })
            else:
                start = new_state()
                end = new_state()
                stack.append({
                    'start': start,
                    'accept': {end},
                    'states': {start, end},
                    'alphabet': {token},
                    'transitions': {(start, token): {end}}
                })
        nfa = stack.pop()
        return nfa

    postfix = to_postfix(regex)
    nfa_dict = postfix_to_nfa(postfix)
    return NFA(
        nfa_dict['states'],
        set(a for a in nfa_dict['alphabet'] if a != ''),
        nfa_dict['transitions'],
        nfa_dict['start'],
        nfa_dict['accept']
    )