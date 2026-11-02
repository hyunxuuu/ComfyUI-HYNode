import enum
import math

class RowState(enum.Enum):
    NAME = 0
    COMMA = 1
    ARGS = 2

class TokenType(enum.Enum):
    NUMBER = 1
    STRING = 2
    BOOL = 3
    COMMA = 4
    NL = 5
    EOF = 6
    ERROR = 7

class Token:
    def __init__(self):
        self.type = TokenType.ERROR
        self.value = None
        self.start = 0
        self.length = 0
        self.mesg = None

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, start={self.start}, length={self.length})"

def token_lexer(token, text, base):
    
    def peek(i):
        pos = base + i
        if pos < 0 or pos >= len(text):
            return "\0"
        return text[pos]
    
    offset = 0
    decimal = False
    escape = False

    token.type = TokenType.ERROR

    while peek(offset) == " " or peek(offset) == "\t":
        offset += 1

    token.start = offset

    if peek(offset) == "-":
        offset += 1
        if not peek(offset).isdigit():
            return 1

    if peek(offset).isdigit():
        if peek(offset) == "0" and peek(offset + 1).isdigit():
            return 1

        while peek(offset).isdigit():
            offset += 1

        if peek(offset) == ".":
            decimal = True
            offset += 1
            if not peek(offset).isdigit():
                token.mesg = "Floating-point parsing error."
                return 1

            while peek(offset).isdigit():
                offset += 1

            if peek(offset) in ("e", "E"):
                exp_offset = 1 if peek(offset + 1) in ("+", "-") else 0
                if peek(offset + 1 + exp_offset).isdigit():
                    offset += 1 + exp_offset
                    while peek(offset).isdigit():
                        offset += 1

        raw = text[base + token.start : base + offset]

        token.type = TokenType.NUMBER
        if decimal:
            token.value = float(raw)
        else:
            token.value = int(raw)
        
        if isinstance(token.value, float) and math.isinf(token.value):
            token.mesg = "Floating-point overflow."
            token.type = TokenType.ERROR
            return 1

        token.length = offset - token.start
        return 0

    if peek(offset) == ",":
        offset += 1
        token.type = TokenType.COMMA
        token.length = offset - token.start
        return 0

    if peek(offset) == "\"":
        offset += 1
        token.start = offset
        token.value = []
        
        while peek(offset) != "\0":
            if peek(offset) == "\\" and not escape:
                escape = True
                offset += 1
                continue

            if peek(offset) == "\"" and not escape:
                break

            token.value.append(peek(offset))
            escape = False
            offset += 1

        if peek(offset) == "\0":
            token.mesg = "Unclosed string."
            return 1

        offset += 1
        token.value = "".join(token.value)
        token.type = TokenType.STRING
        if token.value == "$True":
            token.value = True
            token.type = TokenType.BOOL
        elif token.value == "$False":
            token.value = False
            token.type = TokenType.BOOL
        token.length = offset - token.start
        return 0

    if peek(offset) == "\r":
        offset += 1
        if peek(offset) != "\n":
            token.mesg = "Invalid line break."
            return 1

    if peek(offset) == "\n":
        offset += 1
        token.type = TokenType.NL
        token.length = offset - token.start
        return 0

    if peek(offset) == "\0":
        offset += 1
        token.type = TokenType.EOF
        token.length = offset - token.start
        return 0

    return 1

def csv_report(mesg, text, pos, token, state, row):
    line_no = text.count("\n", 0, pos) + 1
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    col = pos - line_start + 1
    
    if line_end == -1:
        line_end = len(text)

    if mesg == "":
        out = [f"Parsing Error: {token.mesg}"]
    else:
        out = [f"{mesg}"]
    out.append(f"  Position: Line {line_no} , Column {col}")
    out.append(f"  Current record: {row}")
    
    return "\n".join(out)

def csv_lexer(csv_text, csv_list):

    offset = 0
    curr_row = []

    token = Token()
    token.type = TokenType.ERROR
    line_state = RowState.NAME

    while token.type != TokenType.EOF:
        
        if token_lexer(token, csv_text, offset) != 0:
            return csv_report("", csv_text, offset, token, line_state, curr_row)
            
        offset = offset + token.start + token.length

        if line_state == RowState.NAME:
            if token.type == TokenType.STRING:
                curr_row.append(token.value)
                line_state = RowState.COMMA
                continue
                    
            if token.type == TokenType.NL:
                csv_list.append(curr_row)
                curr_row = []
                break
                
            if token.type == TokenType.EOF:
                csv_list.append(curr_row)
                curr_row = []
                break

        if line_state == RowState.COMMA:
            if token.type == TokenType.COMMA:
                line_state = RowState.NAME
                continue
                    
            if token.type == TokenType.NL:
                csv_list.append(curr_row)
                curr_row = []
                break
                
            if token.type == TokenType.EOF:
                csv_list.append(curr_row)
                curr_row = []
                break
                
        return csv_report(f"Format Error: CSV header needs {RowState(line_state).name}", csv_text, offset - token.start - token.length, token, line_state, curr_row)

    token.type = TokenType.ERROR
    line_state = RowState.NAME
    
    while token.type != TokenType.EOF:
        
        if token_lexer(token, csv_text, offset) != 0:
            return csv_report("", csv_text, offset, token, line_state, curr_row)
            
        offset = offset + token.start + token.length

        if line_state == RowState.NAME:
            if token.type == TokenType.STRING:
                curr_row.append(token.value)
                line_state = RowState.COMMA
                continue
                    
            if token.type == TokenType.NL:
                continue
                
            if token.type == TokenType.EOF:
                break

        if line_state == RowState.COMMA:
            if token.type == TokenType.COMMA:
                line_state = RowState.ARGS
                continue
                    
            if token.type == TokenType.NL:
                csv_list.append(curr_row)
                curr_row = []
                line_state = RowState.NAME
                continue
                
            if token.type == TokenType.EOF:
                csv_list.append(curr_row)
                curr_row = []
                break

        if line_state == RowState.ARGS:
            if token.type == TokenType.NUMBER or token.type == TokenType.STRING or token.type == TokenType.BOOL:
                curr_row.append(token.value)
                line_state = RowState.COMMA
                continue
                    
            if token.type == TokenType.NL:
                csv_list.append(curr_row)
                curr_row = []
                line_state = RowState.NAME
                continue
                
            if token.type == TokenType.EOF:
                csv_list.append(curr_row)
                curr_row = []
                break

        return csv_report(f"Format Error: CSV record needs {RowState(line_state).name}", csv_text, offset - token.start - token.length, token, line_state, curr_row)
            
    return ""
    