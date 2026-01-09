import tornado.web
import json
import traceback

ACTIVITY_MAP = {
    "1-A1": lambda code: run_tests_for_imc(code),
    "1-A2": lambda code: run_tests_for_reverse_string(code),
    "3-A1": lambda code: run_manual_check(code),
    "4-A1": lambda code: run_manual_check(code),
    "5-A1": lambda code: run_manual_check(code),
    "9-A1": lambda code: run_manual_check(code),
    "11-A1": lambda code: run_manual_check(code),
}
def run_tests_for_imc(code: str) -> tuple[bool, str]:
    """Testa a função 'calcular_imc(peso, altura)'."""
    test_cases = [
        (80, 1.80, 24.69),
        (60, 1.70, 20.76),
        (100, 2.00, 25.00),
    ]
    
    code_with_tests = f"{code}\n"
    
    try:
        exec_globals = {}
        exec(code_with_tests, exec_globals)
        
        if 'calcular_imc' not in exec_globals:
            return False, "Erro: A função 'calcular_imc' não foi definida no seu código."

        calcular_imc = exec_globals['calcular_imc']
        
        for weight, height, expected_imc in test_cases:
            result = calcular_imc(weight, height)
            
            if abs(result - expected_imc) > 0.01:
                return False, (
                    f"Falha no teste: Entrada ({weight}kg, {height}m). "
                    f"Esperado: {expected_imc:.2f}, Recebido: {result:.2f}"
                )
        
        return True, "Parabéns! Todos os testes para a Calculadora de IMC passaram."
    
    except Exception as e:
        return False, f"Erro de execução no seu código: {type(e).__name__}: {e}"

def run_tests_for_reverse_string(code: str) -> tuple[bool, str]:
    """Testa a função 'inverter_string(texto)'."""
    test_cases = [
        ("Python", "nohtyP"),
        ("hello", "olleh"),
        ("a", "a"),
        ("", ""),
    ]

    code_with_tests = f"{code}\n"
    
    try:
        exec_globals = {}
        exec(code_with_tests, exec_globals)
        
        if 'inverter_string' not in exec_globals:
            return False, "Erro: A função 'inverter_string' não foi definida no seu código."

        inverter_string = exec_globals['inverter_string']
        
        for input_text, expected_output in test_cases:
            result = inverter_string(input_text)
            
            if result != expected_output:
                return False, (
                    f"Falha no teste: Entrada ('{input_text}'). "
                    f"Esperado: '{expected_output}', Recebido: '{result}'"
                )
        
        return True, "Parabéns! A função de inversão de string está correta."
    
    except Exception as e:
        return False, f"Erro de execução no seu código: {type(e).__name__}: {e}"

def run_manual_check(code: str) -> tuple[bool, str]:
    """Verifica atividades manuais/teóricas."""
    if code.strip():
        return True, "Submissão registrada. Atividade concluída."
    return False, "Por favor, preencha o campo de texto."

class SubmitCodeHandler(tornado.web.RequestHandler):
    
    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")
        self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

    def options(self):
        self.set_status(204)
        self.finish()

    def post(self):
        try:
            data = json.loads(self.request.body)
            activity_id = data.get("activity_id")
            submitted_code = data.get("submitted_code")

            if not activity_id or submitted_code is None:
                self.set_status(400)
                self.write({"detail": "Dados de submissão incompletos."})
                return
            
            if activity_id not in ACTIVITY_MAP:
                self.set_status(404)
                self.write({"detail": "ID da atividade não encontrado."})
                return

            test_function = ACTIVITY_MAP[activity_id]
            passed, message = test_function(submitted_code)

            response = {
                "activity_id": activity_id,
                "passed": passed,
                "message": message,
            }
            
            self.set_header("Content-Type", "application/json")
            self.write(response)

        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"detail": "Formato JSON inválido."})
        except Exception as e:
            print(f"Erro no servidor: {traceback.format_exc()}")
            self.set_status(500)
            self.write({"detail": f"Erro interno do servidor: {e}"})