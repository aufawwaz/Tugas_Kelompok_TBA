from collections import defaultdict, deque

class DFA:
    def __init__(self, states, alphabet, transition, start, accept):
        self.states = states
        self.alphabet = alphabet
        self.transition = transition 
        self.start = start
        self.accept = accept

    def test(self, string):
        state = self.start
        for symbol in string:
            state = self.transition.get((state, symbol))
            if state is None:
                return False
        return state in self.accept

    def minimize(self):
        P = [set(self.accept), set(self.states) - set(self.accept)]
        W = [set(self.accept)]
        while W:
            A = W.pop()
            for c in self.alphabet:
                X = set(s for s in self.states if self.transition.get((s, c)) in A)
                for Y in P[:]:
                    inter = X & Y
                    diff = Y - X
                    if inter and diff:
                        P.remove(Y)
                        P.append(inter)
                        P.append(diff)
                        if Y in W:
                            W.remove(Y)
                            W.append(inter)
                            W.append(diff)
                        else:
                            W.append(inter if len(inter) <= len(diff) else diff)

        group_list = [frozenset(group) for group in P]
        state_map = {}
        for group in group_list:
            for s in group:
                state_map[s] = group

        new_states = set(group_list)
        new_start = state_map[self.start]
        new_accept = {state_map[s] for s in self.accept}
        new_transition = {}
        for (s, c), t in self.transition.items():
            new_s = state_map[s]
            new_t = state_map[t]
            new_transition[(new_s, c)] = new_t

        def state_name(s):
            return "{" + ",".join(sorted(s)) + "}"

        str_state_map = {group: state_name(group) for group in new_states}

        str_states = set(str_state_map.values())
        str_start = str_state_map[new_start]
        str_accept = {str_state_map[s] for s in new_accept}
        str_transition = {}
        for (s, c), t in new_transition.items():
            str_transition[(str_state_map[s], c)] = str_state_map[t]

        return DFA(str_states, self.alphabet, str_transition, str_start, str_accept)


    def is_equivalent(self, other):
        def next_state(pair, symbol):
            s1, s2 = pair
            t1 = self.transition.get((s1, symbol))
            t2 = other.transition.get((s2, symbol))
            return (t1, t2)
        visited = set()
        queue = deque()
        queue.append((self.start, other.start))
        while queue:
            s1, s2 = queue.popleft()
            if (s1 in self.accept) != (s2 in other.accept):
                return False
            for c in self.alphabet | other.alphabet:
                pair = next_state((s1, s2), c)
                if pair not in visited and None not in pair:
                    visited.add(pair)
                    queue.append(pair)
        return True

def complete_dfa(states, alphabet, transitions, start, accept):
    states = set(states)
    transitions = dict(transitions)
    dead_state = 'DEAD'
    added_dead = False
    for s in states:
        for c in alphabet:
            if (s, c) not in transitions:
                transitions[(s, c)] = dead_state
                added_dead = True
    if added_dead:
        states.add(dead_state)
        for c in alphabet:
            transitions[(dead_state, c)] = dead_state
    return states, alphabet, transitions, start, accept