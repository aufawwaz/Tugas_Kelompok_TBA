from flask import Flask, render_template, request, jsonify
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
    def new_state():
        new_state.counter += 1
        return f"S{new_state.counter}"
    new_state.counter = -1

    def to_postfix(regex):
        precedence = {'+' : 1,'*': 3, '.': 2, '|': 1}
        output = []
        stack = []
        prev = None
        for c in regex:
            if c in {'(', '|', '*', '+'}:
                if c == '(': 
                    stack.append(c)
                elif c == '|' or c == '+':
                    while stack and stack[-1] != '(' and precedence[stack[-1]] >= precedence[c]:
                        output.append(stack.pop())
                    stack.append(c)
                elif c == '*':
                    output.append(c)
            elif c == ')':
                while stack and stack[-1] != '(': 
                    output.append(stack.pop())
                stack.pop()
            else:
                if prev and (prev not in {'(', '|', '+'} and prev != '.'):
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

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('layout.html')

@app.route('/testdfa', methods=['GET', 'POST'])
def testdfa():
    result = None
    error = None
    if request.method == 'POST':
        states = request.form['states'].strip()
        alphabet = request.form['alphabet'].strip()
        start = request.form['start'].strip()
        accept = request.form.getlist('accept')
        transitions_raw = request.form['transitions'].strip()
        test_str = request.form['teststring'].strip()

        if not (states and alphabet and start and accept and transitions_raw):
            error = "Harap masukkan semua input yang dibutuhkan."
        else:
            states = set(states.split())
            alphabet = set(alphabet)
            accept = set(accept)
            transitions = {}
            for line in transitions_raw.split('\n'):
                if line.strip():
                    s, c, t = line.strip().split()
                    transitions[(s, c)] = t
            dfa = DFA(states, alphabet, transitions, start, accept)
            result = 'Diterima' if dfa.test(test_str) else 'Tidak diterima'
    
    return render_template('testdfa.html', result=result, error=error)


@app.route('/regex', methods=['GET', 'POST'])
def regex():
    result = None
    nfa_obj = None
    regex_input = ''
    error = None

    if request.method == 'POST':
        regex_input = request.form['regex'].strip()
        test_str = request.form['teststring'].strip()

        if not regex_input:
            error = "Harap masukkan regex."
        else:
            nfa_obj = regex_to_nfa(regex_input)
            result = 'Diterima' if nfa_obj.test(test_str) else 'Tidak diterima'
        
    return render_template('regex.html', result=result, nfa_obj=nfa_obj, regex=regex_input, error=error)


@app.route('/minimize', methods=['GET', 'POST'])
def minimize():
    min_dfa = None
    error = None
    minimized = None

    if request.method == 'POST':
        states = request.form['states'].strip()
        alphabet = request.form['alphabet'].strip()
        start = request.form['start'].strip()
        accept = request.form['accept'].strip()
        transitions_raw = request.form['transitions'].strip()

        if not (states and alphabet and start and accept and transitions_raw):
            error = "Harap masukkan semua input yang dibutuhkan."
        else:
            states = set(states.split())
            alphabet = set(alphabet)
            accept = set(accept.split())
            transitions = {}
            for line in transitions_raw.split('\n'):
                if line.strip():
                    s, c, t = line.strip().split()
                    transitions[(s, c)] = t
            dfa = DFA(states, alphabet, transitions, start, accept)
            min_dfa = dfa.minimize()
            minimized = dfa_to_str(min_dfa)

    return render_template('minimize.html', minimized=minimized, error=error)


@app.route('/equivalence', methods=['GET', 'POST'])
def equivalence():
    result = None
    error = None

    if request.method == 'POST':
        required_fields = ['states1', 'alphabet1', 'start1', 'accept1', 'transitions1',
                           'states2', 'alphabet2', 'start2', 'accept2', 'transitions2']
        if not all(request.form[field].strip() for field in required_fields):
            error = "Harap masukkan semua input untuk kedua DFA."
        else:
            states1 = set(request.form['states1'].split())
            alphabet1 = set(request.form['alphabet1'])
            start1 = request.form['start1']
            accept1 = set(request.form['accept1'].split())
            transitions1 = {}
            for line in request.form['transitions1'].split('\n'):
                if line.strip():
                    s, c, t = line.strip().split()
                    transitions1[(s, c)] = t
            dfa1 = DFA(states1, alphabet1, transitions1, start1, accept1)

            states2 = set(request.form['states2'].split())
            alphabet2 = set(request.form['alphabet2'])
            start2 = request.form['start2']
            accept2 = set(request.form['accept2'].split())
            transitions2 = {}
            for line in request.form['transitions2'].split('\n'):
                if line.strip():
                    s, c, t = line.strip().split()
                    transitions2[(s, c)] = t
            dfa2 = DFA(states2, alphabet2, transitions2, start2, accept2)

            result = 'Equivalen' if dfa1.is_equivalent(dfa2) else 'Tidak equivalen'

    return render_template('equivalence.html', result=result, error=error)


def dfa_to_str(dfa):
    s = []
    s.append(f"States: {' '.join(sorted(dfa.states))}")
    s.append(f"Alphabet: {' '.join(sorted(dfa.alphabet))}")
    s.append(f"Start: {dfa.start}")
    s.append(f"Accept: {' '.join(sorted(dfa.accept))}")
    s.append("Transitions:")
    for (src, sym), dst in dfa.transition.items():
        s.append(f"  {src} - {sym} -> {dst}")
    return '\n'.join(s)

if __name__ == '__main__':
    app.run(debug=True)
