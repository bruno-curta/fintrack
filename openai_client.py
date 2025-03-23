import numpy as np

def aiplaceholder(question):
    # generate a randon number from 1 to 10
    # create a list of 10 random messages
    # return one of the messages
    # this is a placeholder for the real AI

    messages = [
        "What ten son the you?",
        "Vai pesquisar sozinho, preguiçoso! Tá achando que eu sou o Google?",
        "Desculpa, não entendi. Pode repetir?",
        "Não sei o que responder. Pergunta pro Bruno!",
        "Não sei, mas a resposta é 42.",
        "Não sei a pergunta, mas a resposta é cerveja!",
        "Era uma vez um gato xadrez...",
        "Pergunta para sua mãe!",
        "Eu tenho cara de quem sabe tudo?",
        "Se eu soubesse, não estaria aqui respondendo para um humano!"
    ]

    return np.random.choice(messages)
