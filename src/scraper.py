from bs4 import BeautifulSoup
from urllib.request import urlopen
import ssl

def process_menu_string_goiabeiras(text):
    if text.startswith('['):
        text = text[1:]
    
    text = text.replace(', Salada', ' Salada')
    text = text.replace(',Salada', ' Salada')
    
    text = text.replace('Salada', '\n\nSalada')
    
    words_to_add_newline = [
        'Prato Principal',
        'Opção',
        'Acompanhamento',
        'Guarnição',
        'Sobremesa'
    ]
    
    for word in words_to_add_newline:
        text = text.replace(word, '\n' + word)

    words_to_add_bold = words_to_add_newline + ['Salada']

    for word in words_to_add_bold:
        text = text.replace(word, '*' + word + '*')
    
    lines_to_remove = [
        '* Cardápio sujeito a alterações.',
        '** Informamos que todas as nossas preparações podem conter traços de glúten e leite (contaminação cruzada).'
    ]
    
    for line in lines_to_remove:
        text = text.replace(line, '')
    
    text = text.replace(', Jantar', 'Jantar')
    text = text.replace(',Jantar', 'Jantar')
    text = text.replace('\n\n\nJantar', '\nJantar')
    
    text = text.replace(', , ]', '')
    
    return text.strip()

def process_menu_string(text, campus="GOIABEIRAS"):

    if campus.upper() == "GOIABEIRAS":
        return process_menu_string_goiabeiras(text)
    
    if text.startswith('['):
        text = text[1:]
    
    # Clean up footer notes
    text = text.replace('* O cardápio poderá sofrer alterações sem comunicação prévia, de acordo com as necessidades do Setor de Nutrição.', '')
    text = text.replace('** Informamos que todas as nossas preparações podem conter traços de glúten e lactose (contaminação cruzada).', '')
    text = text.replace('* Cardápio sujeito a alterações.', '')
    text = text.replace('** Informamos que todas as nossas preparações podem conter traços de glúten e leite (contaminação cruzada).', '')
    
    # Clean up allergen info
    text = text.replace('CG = Contém Glúten', '')
    text = text.replace('CL = Contém Lactose', '')
    text = text.replace('CL= Contém Lactose', '')
    
    # Alegre e Jerônimo Monteiro campus has café, almoço, and jantar
    text = text.replace('Café da Manhã (Alegre e Jerônimo Monteiro)', '\n\n*CAFÉ DA MANHÃ*')
    text = text.replace('Almoço (Alegre e Jerônimo Monteiro)', '\n\n*ALMOÇO*')
    text = text.replace('Jantar (Alegre e Jerônimo Monteiro)', '\n\n*JANTAR*')


    # Add formatting to meal subsections with spacing
    sections_to_format = [
        'Pão',
        'Complemento',
        'Bebida',
        'Fruta',
        'Entrada',
        'Salada',
        'Prato Proteico',
        'Prato Principal',
        'Opção',
        'Acompanhamento',
        'Guarnição',
        'Sobremesa',
        'Suco'
    ]
    
    for section in sections_to_format:
        # Add spacing before each section
        text = text.replace(f'{section}:', f'\n\n*{section}:*\n')
        text = text.replace(f', {section}', f'\n\n*{section}:*')
        text = text.replace(f',{section}', f'\n\n*{section}:*')
    
    # Clean up extra commas and formatting issues
    text = text.replace(', , ]', '')
    text = text.replace(',,', '')
    text = text.replace(', ,', '')
    
    # Remove extra whitespace from lines but keep line breaks
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    
    text = '\n'.join(lines)
    
    # Normalize spacing - no more than double line breaks
    while '\n\n\n' in text:
        text = text.replace('\n\n\n', '\n\n')
    
    return text.strip()

def campus_to_menu(campus):
    menus = {
        "GOIABEIRAS": "https://ru.ufes.br/cardapio",
        "ALEGRE": "https://restaurante.alegre.ufes.br/cardapio",
    }
    return menus.get(campus, "https://ru.ufes.br/cardapio")

def get_menu(campus):
    url = campus_to_menu(campus)
    # ssl
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    html = urlopen(url, context=context).read()

    soup = BeautifulSoup(html, "html.parser")

    content_html = soup.find_all(class_ = "field-content")
    content_soup = BeautifulSoup(str(content_html), "html.parser")

    content = content_soup.get_text()

    menu = process_menu_string(content, campus)

    if menu.startswith('['):
       return "Menu still not available for today..."

    return menu
