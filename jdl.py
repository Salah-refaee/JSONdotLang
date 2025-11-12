from copy import deepcopy
from functools import reduce

class ReturnValue(Exception):
    """Exception to handle function returns"""
    def __init__(self, value):
        self.value = value
        super().__init__()

class BreakLoop(Exception):
    """Exception to handle break statements"""
    pass

class ContinueLoop(Exception):
    """Exception to handle continue statements"""
    pass

class ScopeException(Exception):
    """Exception to use with Scopes (if any error occurred)"""
    pass

class CallFrame:
    """Represents a single frame in the call stack"""
    def __init__(self, name, instruction, line_number=None):
        self.name = name  # Function name or context (e.g., "main", "func1")
        self.instruction = instruction  # The instruction being executed
        self.line_number = line_number  # Optional line number
    
    def __str__(self):
        instr_str = str(self.instruction)
        if len(instr_str) > 60:
            instr_str = instr_str[:57] + "..."
        
        if self.line_number is not None:
            return f"  at {self.name} (line {self.line_number}): {instr_str}"
        else:
            return f"  at {self.name}: {instr_str}"

class CallStack:
    """Manages the call stack for error tracebacks"""
    def __init__(self):
        self.frames = []
    
    def push(self, name, instruction, line_number=None):
        """Add a frame to the call stack"""
        self.frames.append(CallFrame(name, instruction, line_number))
    
    def pop(self):
        """Remove the top frame from the call stack"""
        if self.frames:
            self.frames.pop()
    
    def get_traceback(self):
        """Get formatted traceback string"""
        if not self.frames:
            return ""
        
        lines = []
        for frame in self.frames:
            lines.append(str(frame))
        return "\n".join(lines)
    
    def clear(self):
        """Clear the call stack"""
        self.frames.clear()

class Scope:
    def __init__(self, parent=None):
        self.parent = parent
        self.locals = {}
    
    def set(self, name, value):
        self.locals[name] = value
    
    def get(self, name):
        if name in self.locals:
            value = self.locals[name]
            if isinstance(value, Func):
                return value
            return deepcopy(value)
        
        if self.parent:
            return self.parent.get(name)
        
        raise NameError(f"Name '{name}' not defined")
    
    def export(self, *names):
        if self.parent:
            for name in names:
                self.parent.set(name, self.get(name))
        else:
            raise ScopeException("Can't export a value to the Global Scope while already working in the global scope")
    
    def is_global_func_exists(self, funcname):
        try:
            value = self.get(funcname)
            return isinstance(value, Func)
        except NameError:
            return False

class Func:
    def __init__(self, params, body, name):
        self.params = params
        self.body = body
        self.name = name
    
    def __str__(self):
        return f"<func {self.name}({', '.join(self.params)})>"
    
    def __repr__(self):
        return f"Func(name={self.name}, params={self.params})"

class Lang:
    def __init__(self, scope: Scope, code: tuple, call_stack=None, context_name="<string>"):
        self.scope = scope
        self.code = code
        self.call_stack = call_stack if call_stack is not None else CallStack()
        self.context_name = context_name
    
    def resolve_value(self, value):
        """Resolve a value - handle variable references, arrays, dicts"""
        if isinstance(value, str) and value.startswith("$"):
            return self.scope.get(value[1:])
        elif isinstance(value, tuple) and len(value) > 0:
            return self.execute_instruction(value)
        elif isinstance(value, list):
            return [self.resolve_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self.resolve_value(v) for k, v in value.items()}
        else:
            return value
    
    def flatten_arithmetic(self, instr, args):
        """Flatten deeply nested arithmetic operations for better performance"""
        ops = {
            '+': lambda a, b: a + b,
            '-': lambda a, b: a - b,
            '*': lambda a, b: a * b,
            '/': lambda a, b: a / b,
            '%': lambda a, b: a % b,
        }
        
        if instr not in ops:
            return None
        
        stack = list(args)
        values = []
        
        while stack:
            item = stack.pop(0)
            
            if (isinstance(item, (list, tuple)) and len(item) > 0 and 
                item[0] == instr):
                stack = list(item[1:]) + stack
            else:
                values.append(self.resolve_value(item))
        
        return reduce(ops[instr], values)
    
    def execute_instruction(self, loc, line_number=None):
        """Execute a single instruction and return its result"""
        #print("DebugLOC:", loc)
        instr = loc[0]
        #print("DebugInstr:", instr)
        args = loc[1:]
        
        # Push current instruction to call stack
        self.call_stack.push(self.context_name, loc, line_number)
        
        try:
            match instr:
                case "exit":
                    if len(args) == 0:
                        raise SystemExit(0)
                    elif len(args) == 1:
                        raise SystemExit(args[0])
                    else:
                        raise ValueError(f"{instr} takes 1 optional argument")
                
                case "var":
                    if len(args) != 2:
                        raise SyntaxError(f"{instr} takes 2 arguments")
                    name, value = args
                    resolved_value = self.resolve_value(value)
                    self.scope.set(name, resolved_value)
                    return resolved_value
                
                case "int":
                    if len(args) != 1:
                        raise SyntaxError("{instr} takes 1 argument")
                    value = self.resolve_value(args[0])
                    return int(value)
                
                case "str":
                    if len(args) != 1:
                        raise SyntaxError("{instr} takes 1 argument")
                    value = self.resolve_value(args[0])
                    return str(value)
                
                case "float":
                    if len(args) != 1:
                        raise SyntaxError("{instr} takes 1 argument")
                    value = self.resolve_value(args[0])
                    return float(value)
                
                case "bool":
                    if len(args) != 1:
                        raise SyntaxError("{instr} takes 1 argument")
                    value = self.resolve_value(args[0])
                    return bool(value)
                
                case "func":
                    if len(args) != 3:
                        raise SyntaxError(f"{instr} takes 3 arguments (name, params, body)")
                    name, params, body = args
                    func = Func(params, body, name)
                    self.scope.set(name, func)
                    return func
                
                case "return":
                    if len(args) == 0:
                        raise ReturnValue(None)
                    elif len(args) == 1:
                        value = self.resolve_value(args[0])
                        raise ReturnValue(value)
                    else:
                        values = tuple(self.resolve_value(a) for a in args)
                        raise ReturnValue(values)
                
                case "break":
                    raise BreakLoop()
                
                case "continue":
                    raise ContinueLoop()
                
                case "export":
                    self.scope.export(*args,)
                
                case "if":
                    if len(args) < 2 or len(args) > 3:
                        raise SyntaxError(f"{instr} takes 2 or 3 arguments (condition, then_body, [else_body])")
                    
                    condition = self.resolve_value(args[0])
                    then_body = args[1]
                    else_body = args[2] if len(args) == 3 else None
                    
                    if condition:
                        if isinstance(then_body, (list, tuple)):
                            return Lang(self.scope, then_body, self.call_stack, self.context_name).run()
                        else:
                            return self.execute_instruction(then_body)
                    elif else_body:
                        if isinstance(else_body, (list, tuple)):
                            return Lang(self.scope, else_body, self.call_stack, self.context_name).run()
                        else:
                            return self.execute_instruction(else_body)
                    return None
                
                case "while":
                    if len(args) != 2:
                        raise SyntaxError(f"{instr} takes 2 arguments (condition, body)")
                    
                    condition_expr = args[0]
                    body = args[1]
                    result = None
                    
                    while True:
                        if isinstance(condition_expr, tuple):
                            condition = self.execute_instruction(condition_expr)
                        else:
                            condition = self.resolve_value(condition_expr)
                        
                        if not condition:
                            break
                        
                        try:
                            if isinstance(body, (list, tuple)):
                                result = Lang(self.scope, body, self.call_stack, self.context_name).run()
                            else:
                                result = self.execute_instruction(body)
                        except BreakLoop:
                            break
                        except ContinueLoop:
                            continue
                    
                    return result
                
                case "for":
                    if len(args) != 3:
                        raise SyntaxError(f"{instr} takes 3 arguments (var_name, iterable, body)")
                    
                    var_name = args[0]
                    iterable = self.resolve_value(args[1])
                    body = args[2]
                    result = None
                    
                    for item in iterable:
                        self.scope.set(var_name, item)
                        
                        try:
                            if isinstance(body, (list, tuple)):
                                result = Lang(self.scope, body, self.call_stack, self.context_name).run()
                            else:
                                result = self.execute_instruction(body)
                        except BreakLoop:
                            break
                        except ContinueLoop:
                            continue
                    
                    return result
                
                case "get":
                    if len(args) != 1:
                        raise SyntaxError(f"{instr} takes 1 argument")
                    return self.scope.get(args[0])
                
                case "print":
                    resolved = [self.resolve_value(a) for a in args]
                    print(*resolved, end='')
                    return resolved if len(resolved) > 1 else resolved[0]
                
                case "input":
                    if len(args) > 1:
                        raise SyntaxError(f"{instr} takes no/one argument")
                    
                    if not args:
                        return input()
                    match args[0]:
                        case "int":   return int(input())
                        case "float": return float(input())
                        case "str":   return input()
                        case "bool":  return bool(input())
                        case _:
                            raise TypeError("unknown data type: " + str(args[0]))
                
                case "array":
                    return [self.resolve_value(arg) for arg in args]
                
                case "dict":
                    if len(args) % 2 != 0:
                        raise SyntaxError("dict requires even number of arguments (key-value pairs)")
                    result = {}
                    for i in range(0, len(args), 2):
                        key = self.resolve_value(args[i])
                        value = self.resolve_value(args[i + 1])
                        result[key] = value
                    return result
                
                case "index":
                    if len(args) != 2:
                        raise SyntaxError(f"{instr} takes 2 arguments (container, index)")
                    container = self.resolve_value(args[0])
                    index = self.resolve_value(args[1])
                    return container[index]
                
                case "len":
                    if len(args) != 1:
                        raise SyntaxError(f"{instr} takes 1 argument")
                    value = self.resolve_value(args[0])
                    return len(value)
                
                case "switch":
                    if len(args) < 2:
                        raise SyntaxError(f"{instr} expects at least 2 arguments (value, cases...)")
                    
                    value = self.resolve_value(args[0])
                    cases = args[1:-1]  # all except the last argument
                    default_block = args[-1] if isinstance(args[-1], list) else None
                    
                    executed = False
                    
                    for case_dict in cases:
                        if not isinstance(case_dict, dict):
                            raise TypeError("Each case must be a dict like {value: [code]}")
                        
                        for case_value, case_body in case_dict.items():
                            case_value_resolved = self.resolve_value(case_value)
                            if value == case_value_resolved:
                                executed = True
                                if isinstance(case_body, (list, tuple)):
                                    return Lang(self.scope, case_body, self.call_stack, self.context_name).run()
                                else:
                                    return self.execute_instruction(case_body)
                    
                    # Default case
                    if not executed and default_block:
                        if isinstance(default_block, (list, tuple)):
                            return Lang(self.scope, default_block, self.call_stack, self.context_name).run()
                        else:
                            return self.execute_instruction(default_block)
                    
                    return None
                case _:
                    
                    if instr in ['+', '-', '*', '/', '%']:
                        result = self.flatten_arithmetic(instr, args)
                        if result is not None:
                            return result
                    
                    if instr in ['==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'not', "!->"]:
                        if instr == 'not':
                            if len(args) != 1:
                                raise SyntaxError(f"{instr} takes 1 argument")
                            return not self.resolve_value(args[0])
                        
                        values = [self.resolve_value(a) for a in args]
                        
                        ops = {
                            '==': lambda a, b: a == b,
                            '!=': lambda a, b: a != b,
                            '<': lambda a, b: a < b,
                            '>': lambda a, b: a > b,
                            '<=': lambda a, b: a <= b,
                            '>=': lambda a, b: a >= b,
                            'and': lambda a, b: a and b,
                            'or': lambda a, b: a or b,
                            '!->': lambda a, b: a not in b # I wish it will work
                        }
                        return reduce(ops[instr], values)
                    
                    if self.scope.is_global_func_exists(instr):
                        call_args = args
                        func = self.scope.get(instr)
                        
                        if len(call_args) != len(func.params):
                            raise SyntaxError(f"{instr} requires {len(func.params)} argument(s), got {len(call_args)}")
                        
                        func_scope = Scope(self.scope)
                        
                        for param, arg in zip(func.params, call_args):
                            resolved_arg = self.resolve_value(arg)
                            func_scope.locals[param] = resolved_arg
                        
                        func_lang = Lang(func_scope, func.body, self.call_stack, func.name)
                        try:
                            func_lang.run()
                            return None
                        except ReturnValue as ret:
                            return ret.value
                    else: 
                        raise SyntaxError(f"Unknown instruction: {instr}")
        
        finally:
            # Pop the frame after execution (success or failure)
            self.call_stack.pop()
    
    def run(self):
        result = None
        i = 0
        for loc in self.code:
            try:
                #TEMPORARY CODE
                if type(loc).__name__ != "tuple":
                    loc = (loc,)
                #END
               # print("DebugLOC2:", loc)
                result = self.execute_instruction(loc, line_number=i+1)
            except (ReturnValue, BreakLoop, ContinueLoop):
                # These are control flow exceptions, re-raise them
                raise
            except Exception as e:
                # For any other exception, print traceback and re-raise
                error_name = type(e).__name__
                error_desc = str(e)
                traceback = self.call_stack.get_traceback()
                
                print(f"\n{error_name}: {error_desc}")
                print(traceback)
                raise SystemExit(1)
            i += 1
        return result

if __name__ == "__main__":
    from sys import argv
    from ast import literal_eval
    
    if len(argv) - 1 != 1:
        exit(f"Expected one argument, {str(len(argv) - 1)} given")
    try:
        with open(argv[1], 'r') as f:
            Lang(Scope(), literal_eval(f.read()), context_name=argv[1]).run()
    except FileNotFoundError:
        print(f"\nError: file {argv[1]} not found.")