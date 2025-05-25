from flask import Flask, render_template, request
from pyformlang.regular_expression import Regex
from pyformlang.finite_automaton import State, Symbol, DeterministicFiniteAutomaton

app = Flask(__name__)

# Utilitas untuk parsing form input menjadi DFA
def parse_dfa_form(data):
    try:
        states = set(s.strip() for s in data['states'].split(",") if s.strip())
        symbols = set(s.strip() for s in data['symbols'].split(",") if s.strip())
        start = data['start'].strip()
        final = set(s.strip() for s in data['final'].split(",") if s.strip())
        transitions = data['transitions'].strip().splitlines()

        if not states or not symbols:
            return "Kesalahan: States dan symbols tidak boleh kosong."
        if start not in states:
            return f"Kesalahan: Start state '{start}' tidak ada di daftar states."
        if not final.issubset(states):
            return f"Kesalahan: Final states harus bagian dari states."

        dfa = DeterministicFiniteAutomaton()
        dfa.add_start_state(State(start))
        for f in final:
            dfa.add_final_state(State(f))

        for line in transitions:
            parts = line.split("->")
            if len(parts) != 2:
                return f"Kesalahan format transisi (harus 'state,symbol -> next_state'): {line}"
            left = parts[0].strip().split(",")
            if len(left) != 2:
                return f"Kesalahan format bagian kiri transisi: {line}"
            src, sym = left[0].strip(), left[1].strip()
            dst = parts[1].strip()

            if src not in states:
                return f"State asal '{src}' tidak ada di daftar states."
            if dst not in states:
                return f"State tujuan '{dst}' tidak ada di daftar states."
            if sym not in symbols:
                return f"Simbol '{sym}' tidak ditemukan di daftar simbol."

            dfa.add_transition(State(src), Symbol(sym), State(dst))

        return dfa
    except Exception as e:
        return f"Kesalahan: {str(e)}"


@app.route("/")
def index():
    return render_template("dfa_test.html")


@app.route("/dfa-test", methods=["GET", "POST"])
def dfa_test():
    result = ""
    if request.method == "POST":
        dfa = parse_dfa_form(request.form)
        if isinstance(dfa, str):
            result = f"Error: {dfa}"
        else:
            string = request.form['string']
            try:
                result = "DITERIMA" if dfa.accepts([Symbol(c) for c in string]) else "DITOLAK"
            except Exception as e:
                result = f"Error saat mengecek DFA: {str(e)}"
    return render_template("dfa_test.html", result=result)


@app.route("/regex-test", methods=["GET", "POST"])
def regex_test():
    result = ""
    if request.method == "POST":
        try:
            regex = Regex(request.form['regex'])
            string = request.form['string']
            result = "DITERIMA" if regex.to_epsilon_nfa().accepts([Symbol(c) for c in string]) else "DITOLAK"
        except Exception as e:
            result = f"Error: {str(e)}"
    return render_template("regex_test.html", result=result)


@app.route("/minimize-dfa", methods=["GET", "POST"])
def minimize_dfa():
    result = ""
    if request.method == "POST":
        dfa = parse_dfa_form(request.form)
        if isinstance(dfa, str):
            result = f"Error: {dfa}"
        else:
            try:
                min_dfa = dfa.minimize()
                output = [
                    "States: " + ", ".join(sorted(str(s) for s in min_dfa.states)),
                    "Symbols: " + ", ".join(sorted(str(sym) for sym in min_dfa.symbols)),
                    "Start: " + str(min_dfa.start_state),
                    "Final: " + ", ".join(sorted(str(s) for s in min_dfa.final_states)),
                    "Transitions:"
                ]
                for from_state, trans in min_dfa._transition_function._transitions.items():
                    for symbol, to_state in trans.items():
                        output.append(f"{from_state}, {symbol} -> {to_state}")
                result = "\n".join(output)
            except Exception as e:
                result = f"Error saat minimisasi: {str(e)}"
    return render_template("minimize_dfa.html", result=result)


@app.route("/dfa-equivalence", methods=["GET", "POST"])
def dfa_equivalence():
    result = ""
    if request.method == "POST":
        dfa1 = parse_dfa_form({k[5:]: v for k, v in request.form.items() if k.startswith("dfa1_")})
        dfa2 = parse_dfa_form({k[5:]: v for k, v in request.form.items() if k.startswith("dfa2_")})
        if isinstance(dfa1, str) or isinstance(dfa2, str):
            result = f"Error: {dfa1 if isinstance(dfa1, str) else dfa2}"
        else:
            try:
                result = "EKUIVALEN" if dfa1.minimize() == dfa2.minimize() else "TIDAK EKUIVALEN"
            except Exception as e:
                result = f"Error saat pengecekan ekuivalensi: {str(e)}"
    return render_template("dfa_equivalence.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
