import modules.scripts as scripts
import gradio as gr

import os
import re
from os.path import isfile, join
from os import listdir

from os import path
from modules.paths import script_path
from modules.shared import opts, cmd_opts, state

from modules.processing import process_images, Processed

ResultBefore = {
    "Not set":"", 
    "()":"(", 
    "[]":"["
}

ResultType = {
    "Not set":"", 
    "()":")", 
    "[]":"]"
}

AlwaysBad = ""

Modifier = {
    "None":"",  # Análisis atendiendo a la procedencia de la luz
    "-":"-",    #-	Luz natural (en interior)
    "+":"+",    #+	Luz de Flash
    #	Foco superior cercano (sombras borrosas)
    "!":"!",    #!	Foco lejano (de arriba abajo) imagen bien iluminada
    "?":"?",    #?	Foco aun más lejano (de arriba abajo) más uniformidad en la luz
    "^":"^",    #^	Foco frontal inferior (de abajo arriba)
    "=":"=",    #=	Foco a la altura de la cara
    "&":"&",    #&	Foco inferior cercano lateral (De izq a derecha)
    "$":"$",    #$	Foco frontal lateral (de izq a derecha)
    "*":"*",    #*	Luz lateral extrema cercana (de izq a decha)
    "·":"·",    #·	luz superior lateral suave (de izq a decha)
    "%":"%",    #%	Dos fuentes de luz Frontal y superior tenue
    ".":".",    #.	Luz potente frontal inferior
    ":":":",    #:	Luz potente frontal superior (Presta atención al resto de variables ) Puede desenfocar la imagen
    ";":";",    #;	Luz tenue frontal sombreado suave (Presta atención al resto de variables ) Puede desenfocar la imagen
    "'":"'",    #'	Luz frontal superior potente (similar a ++++)
    ",":",",    #,	Luz solar natural superior potente (Sombras definidas)
    "<":"<",    #<	Luz cenital superior (sombras difusas)
    ">":">",    #>	Luz inferior (Sombras difusas)
    "~":"~",    #~	Luz solar natural directa (Sombras muy definidas)
    "/":"/",    #/	Luz inferior potente (sombras definidas)
    "\\":"\\",  #\	Dos fuentes de Luz frontal directa Flash y superior tenue
    "º":"º",    #º	Luz frontal directa (sombras suavizadas)
    "ª":"ª",    #ª	Luz frontal directa (sombras difusas)
    "¿":"¿",    #¿	Luz frontal directa
    "¡":"¡",    #¡	Luz inferior directa
    "_":"_",    #_	Luz lateral superior (difumina la imagen no es buena técnica en general
    "€":"€",    #€	Luz inferior natural (sombras difuminadas)
    "¬":"¬",    #¬	Luz inferior difusa
    "|":"|",    #|	Luz solar calida mediodia (sombras bien definidas)
    #"":"",    #"	Luz frontal directa (sombras tenues)
    "`":"`",    #`	Luz frontal ligeramente desde abajo
    "´":"´",    #´	Luz frontal desde abajo
    "ñ":"ñ",    #ñ	Luz frontal ligeramente inferior desde la derecha y azul
    "ç":"ç",    #ç	Luz inferior frontal y negro
    "¨":"¨",    #¨	Luz frontal difusa (exagerada y borrosa iluminación)
    "{":"{",    #{	Luz natural lateral (izq a derecha) imágen nítida sombra borrosa
    "}":"}",    #}	Luz frontal superior ligeramente por encima de la cabeza (sombra nítida por abajo borrosa por arriba)
    "#":"#",
    "@":"@",
    #"*":"*"
}

Premod = {
    "None":"",
    "^":"^^",
    "?":"??",
    "¿":"¿¿",
    "-":"--"
}

Attention = {
    "Not set":"", 
    "0.66":":0.66",
    "0.75":":0.75",
    "0.9":":0.9",
    "1.15":":1.15",
    "1.25":":1.25",
    "1.33":":1.33"
}

class Script(scripts.Script):

    def title(self):
        return "Fase1"

    def show(self, is_img2img):
        return True
        
    def ui(self, is_img2img):
        with gr.Tab("Fase1"):
            with gr.Row(variant='panel'):
                sol = gr.Textbox(label="Optional sufix") # Palabra a insertar
                sol2 = gr.Textbox(label="Optional prefix") # Palabra a insertar
                ENE = gr.Slider(1,75,step=1, label="Word") # Convertir en selector de término N = ?                
                
            with gr.Row(variant='panel'):                
                poResultType = gr.Radio(list(ResultType.keys()), label="Capsule type", value="Not set")
                Numero = gr.Slider(1, 3, step=1, label="Times")                
                poAttention = gr.Dropdown(list(Attention.keys()), label="Intensity", value="Not set") # Attention :0.x
                                
            with gr.Row(variant='panel'):
                poModifier = gr.Radio(list(Modifier.keys()), label="Modifiers", value="None")
                quantity = gr.Slider(1, 45, step=1) # Iterations
                
            with gr.Row(variant='panel'):
                poModifier2 = gr.Radio(list(Modifier.keys()), label="Secondary Modifiers", value="None")
                quantity2 = gr.Slider(1, 90, step=1)
                
            with gr.Row(variant='panel'):
                poPremod = gr.Radio(list(Premod.keys()), label="Initial modifiers", value="None")
                
        with gr.Tab("WIKI"):
            gr.Markdown(
                """
                ## WIKI                
                
                ### How to make a low cost animation
                1. Write a prompt and generate your image.
                2. Click on recycle the last seed.
                3. Activate the extension.
                4. Use the first slider to select a word of your prompt (count the position).
                5. On section Modifiers choose one of them, with the slider select the number of iterations of that modifier. If you want play with others options of the extension.
                6. Press Generate and wait.
                
                #### Study of the lights 
                Inference of the the light and the shadows with modifiers. It clould NOT work with complex prompt, in that case you generate only variations like seed travel or denoising.                

                
                | Sym | Spanish   |  English   | Sym |
                |--------|-----------|------------|---|
                | \- | Luz natural (en interior) | Natural lights (inside room) | - |
                | \+ | Luz de Flash | burst of light | \+ |
                | \# | Foco superior cercano (sombras borrosas) | Near upper lights | \# |
                | \! | Foco lejano (de arriba abajo) imagen bien iluminada | Far focus from above, well light | \! |
                | \? | Foco aun más lejano (de arriba abajo) más uniformidad en la luz | Far focus, uniform light | \? |
                | \^ | Foco frontal inferior (de abajo arriba) | Frontal light from below | \^ |
                | \= | Foco a la altura de la cara | Face to face light | \= |
                | \& | Foco inferior cercano lateral (De izq a derecha) | focus from below near to left side | \& |
                | \$ | Foco frontal lateral (de izq a derecha) | Frontal focus, left side | \$ |
                | \* | Luz lateral extrema cercana (de izq a decha) | Extremely near left light | \* |
                | · | Luz superior lateral suave (de izq a decha) | Upper and left side soft light | · |
                | \% | Dos fuentes de luz Frontal y superior tenue | Two lights, frontal and upper soft | \% |
                | \. | Luz potente frontal inferior | High frontal light from below | \. |
                | \: | Luz potente frontal superior (Presta atención al resto de variables ) Puede desenfocar la imagen | High upper frontal light | \: |
                | ; | Luz tenue frontal sombreado suave (Presta atención al resto de variables ) Puede desenfocar la imagen | Soft frontal shadows. It clould blurry the image | ; |
                | \' | Luz frontal superior potente (similar a ++++) | Powerful Frontal up light, similar to use ++++ | \' | 
                | \, | Luz solar natural superior potente (Sombras definidas) | Sun light, well defined shadows | \, |
                | \< | Luz cenital superior (sombras difusas) | Upper light, blur lights | \< |
                | \> | Luz inferior (Sombras difusas) | Lower light, blur shadows | \> |
                | \~ | Luz solar natural directa (Sombras muy definidas) | Direct Sun light, very well defined shadows | \~ |
                | \/ | Luz inferior potente (sombras definidas) | Powerful Lower light, well defined lights | \/ |
                | \\ | Dos fuentes de Luz frontal directa Flash y superior tenue | Two lights frontal light and upper soft light | \\ |
                | º | Luz frontal directa (sombras suavizadas) | Direct frontal light (soft shadows) | º |
                | ª | Luz frontal directa (sombras difusas) | Frontal light (blur shadows) | ª |
                | ¿ | Luz frontal directa | Direct frontal light | ¿ |
                | ¡ | Luz inferior directa | direct light from below | ¡ |
                | _ | Luz lateral superior, difumina la imagen, no es buena técnica en general | Upper side light, blur everything, not good in general | _ |
                | € | Luz inferior natural (sombras difuminadas) | Natural light from below (blur shadows) | € |
                | ¬ | Luz inferior difusa | Soft light from below | ¬ |
                | \| | Luz solar calida mediodia (sombras bien definidas) | Noon Sun light, well defined shadows | \| |
                | \" | Luz frontal directa (sombras tenues) | Frontal light, soft shadows | \" |
                | \` | Luz frontal ligeramente desde abajo | Frontal light from below | \` |
                | ´ | Luz frontal desde abajo | Frontal light from below | ´ |
                | ñ | Luz frontal ligeramente inferior desde la derecha y azul | Slightly below from right side and blue | ñ |
                | ç | Luz inferior frontal y negro | From below and black | ç |
                | ¨ | Luz frontal difusa (exagerada y borrosa iluminación)| Weird frontal light | ¨ |
                | \{ | Luz natural lateral (izq a derecha) imágen nítida sombra borrosa| Natural light left side| \{ | 
                | \} | Luz frontal superior ligeramente por encima de la cabeza (sombra nítida por abajo borrosa por arriba)| Frontal light slightly up from head, shadows well defined below and blurred up | \} |
                | \@ | Sorpresa | Surprise | \@ |
                |0-9| No incluido. Redimensiona la atención, 9999 equivale a un collage (ya no va) | Not included. Resize the attention, 9999 is equal to collage (out-dated) | 0-9 |
                
                If you find other modifiers or you want improve this list with your knowledge (some effects could be banish by changes in Automatic1111 web-ui code) send me your issues or pull request.
               
            """)
                
        return [poResultType, poPremod, poModifier, poModifier2, quantity, quantity2, poAttention, Numero, sol, sol2, ENE]

    def run(self, p, poResultType, poPremod, poModifier, poModifier2, quantity, quantity2, poAttention, Numero, sol, sol2, ENE):
        test0 = p.prompt # extraer prompt
        sol0 = test0.split(' ')[ENE-1] # Extraer N-esima palabra
        solin = re.sub(r'[(|)|[|\]|:1-9.,]', '',sol0) # limpiar caracteres extras en torno a la palabra
        for i in range(0,quantity):                    
            solin0 = sol2 + ResultBefore[poResultType]*Numero + Premod[poPremod] + solin + Attention[poAttention] + ResultType[poResultType]*Numero + Modifier[poModifier]*i + Modifier[poModifier2]*quantity2 + sol # Unir opciones p.prompt
            p.prompt = test0.replace(solin,"".join([solin0])) # sustituye solin en p.prompt
            p.negative_prompt += AlwaysBad

            proc = process_images(p)
        return proc        