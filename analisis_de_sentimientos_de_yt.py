# -*- coding: utf-8 -*-
"""Analisis de sentimientos de YT.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/137L47gF_VaW3TQAe0B0hOGoqYaB6yFZR

#Análisis de datos de un video en youtube.com

Instrucciones:
1. Google developer console (Consola desarollador de google)
2. Generar API KEY
3. Crear Proyecto
4. Habilitar api y servicios
5. Habilitar Youtube Data API v3
6. Crear Credenciales
7. Ir a youtube Data API y referencias
8. Leer la documentación que se encuentra en:
# https://developers.google.com/explorer-help/code-samples
"""

import pandas as pd
import numpy as np
import seaborn as sns

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

#Ejercutar la primera vez que se ejecuta el script para realizar la instalación, luego no es necesario ejecutar esta linea.
!pip install google-api-python-client

from googleapiclient.discovery import build

api_key='Colocar_Aqui_La_API_KEY_Generada_Por_GOOGLE'
#Colocar el ID del canal al cual vas a extraer los videos, en este caso elegí el ID del canal de Comedy Central LA
channel_id='UCJGanRdrtdqYlDPoBEM_C_A' #
#Get youtube services.
youtube=build('youtube','v3',developerKey=api_key)

"""Obteneción de estadísticas del canal"""

def get_channel_stats(yt,ch_id):
  #Hace una petición para obtener las estadísticas del canal deseado.
  request=youtube.channels().list(part='snippet,contentDetails,statistics',id=ch_id)
  response=request.execute()
  data=dict(nombre_Canal=response['items'][0]['snippet']['title'],
            Descripcion_Canal=response['items'][0]['snippet']['description'],
            Suscriptores=response['items'][0]['statistics']['subscriberCount'],
            Vistas_Videos=response['items'][0]['statistics']['viewCount'],
            Numero_Videos=response['items'][0]['statistics']['videoCount'],
            Lista_Reproduccion_ID=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            )
  return data
youtube_stats=get_channel_stats(youtube,channel_id)
youtube_stats

"""Obtención de los vídeos del canal"""

#Los videos subidos quedan guardados en Lista_Reproduccion_ID, así que vamos a acceder a ellos.
Videos_Subidos=youtube_stats['Lista_Reproduccion_ID']

def get_video_ids(yt,playlist):
  #Obtiene la lista de videos del lista de reproduccion seleccionada
  request=yt.playlistItems().list(
      part='contentDetails',
      playlistId=playlist,
      maxResults=50
  )
  response=request.execute()
  video_ids=[]
  for i in range(len(response['items'])):
    video_ids.append(response['items'][i]['contentDetails']['videoId'])
  nextPageToken=response.get('nextPageToken')
  more_pages=True
  while more_pages:
    if nextPageToken is None:
      more_pages=False
    else:
      request=yt.playlistItems().list(
        part='contentDetails',
        playlistId=playlist,
        maxResults=50,
        pageToken=nextPageToken)
      response=request.execute()
      for i in range(len(response['items'])):
        video_ids.append(response['items'][i]['contentDetails']['videoId'])
      nextPageToken=response.get('nextPageToken')
  return (video_ids)

video_ids=get_video_ids(youtube,Videos_Subidos)

"""Obtención de comentarios del video"""

def video_comments(yt,video_id):
    # Obtiene los comentarios de un video deseado, el id se puede obtener ya sea por el método anterior o por el mismo link de youtube.
    replies = []
    # crear el objeto youtube que hara la petición de comentarios
    request=yt.commentThreads().list(
    part='snippet,replies',
    videoId=video_id,
    maxResults=100)
    video_response=request.execute()
    commentsList=[]
    comment_Type=[]
    for item in video_response['items']:
            comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
            replycount = item['snippet']['totalReplyCount']
            commentsList.append(comment)
            if replycount>0:
                for reply in item['replies']['comments']:
                    reply = reply['snippet']['textDisplay']
                    replies.append(reply)
            print(comment, replies, end = '\n\n')
    return  commentsList

youtube_video='kHAqmuBvHg0' #Es uno de los videos que se encuentra en la lista de reproduccion videos subidos del canal.
youtube_comments=video_comments(youtube,youtube_video)

"""Transformación de los comentarios"""

import re
def discard_youtube_comments(ytComments):
  cleanComments=[]
  for comment in ytComments:
    commentWithoutLinks = re.sub(r'http://\S+|https://\S+', '', comment, flags=re.MULTILINE)
    final_comment=commentWithoutLinks.replace('&#39','')
    #final_comment=re.sub(r'\([^)]*\)', '', final_comment) #Añadido para eliminar parentesis
    cleanComments.append(final_comment)
  cleanComments=list(map(str.strip, cleanComments))
  return cleanComments
processedytComments=discard_youtube_comments(youtube_comments)
print(processedytComments)

"""
--Importacion de liberias para análisis de sentimientos"""

import nltk #Procesamiento lenguaje natural
import os #Sistema operativo
import nltk.corpus #Corpus-->conjunto de texto a analizar, se usa para clasificar un texto o incluso una bd

nltk.download('punkt')

"""En este punto ya se tienen los comentarios.
Así que toca preparar los datos en una matriz

#Tokenización
"""

from nltk.tokenize import word_tokenize
from nltk.probability import FreqDist

tokensList=[]
fdistList=[]
mostCommonWordsinComments=[]
for i in range (len(processedytComments)):
  processedytComments[i]=processedytComments[i].lower()
  token=word_tokenize(processedytComments[i]) #Transformo las palabras en una lista
  fdist=FreqDist(token) #Cuenta la frecuencia de las palabras de la lista token
  tokensList.append(token) #Grabo la lista generada, en una lista de listas
  fdistList.append(fdist) #Grabo la lista generada en una lista de listas
  mostComonWords=fdist.most_common(15)
  mostCommonWordsinComments.append(mostComonWords)

"""##Lematización / derivación  y stopwords"""

from nltk.stem import PorterStemmer
from nltk.stem import SnowballStemmer
from nltk import word_tokenize
from nltk.corpus import stopwords
stemmer = SnowballStemmer('spanish')
pst=PorterStemmer()

nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')

palabras_vacias=set(stopwords.words("spanish"))

comment_withoutStopWords=[] #Aqui se guardaran las palabras despues de hacer derivacion
for i in range (len(tokensList)):
  stm=tokensList[i] #Accedo a la lista de listas en la posicion i [ ]
  comment_processed=[]
  for word in  stm:
    print(word+ ";"+ pst.stem(word))
    if word not in palabras_vacias:
      text_without_stopwords=word
      comment_processed.append(text_without_stopwords)
      print(nltk.pos_tag(['word']))
  comment_withoutStopWords.append(comment_processed)

"""Refactorización del dataframe"""

df=pd.DataFrame(youtube_comments,columns=['comentario_youtube'])
processedCommentsDf=[]
for i in range(len(comment_withoutStopWords)):
  tempstring=''
  for word in comment_withoutStopWords[i]:
    tempstring+=word+' '
  text=re.sub(r'#','',tempstring)
  text=re.sub(r'&','',text)
  text=re.sub(r'br','',text)
  text=re.sub(r'@[A-Za-z0-9]+','' ,text)
  text=re.sub(r'\.','',text)
  text=re.sub(r'\(.','',text)
  text=re.sub(r'\).','',text)
  #text=re.sub(r'^.*?\([^\d]*(\d+)[^\d]*\).*$','', text)
  text=text.replace("?","")
  processedCommentsDf.append(text)

df['comentarioProcesado'] = processedCommentsDf
removeFutherElements={'href=':'','<':'','>':'','https':'','quot':'',';':'','"':'',':':'','¡':'','!':'',",":'','¿':''}
df.replace({"comentarioProcesado": removeFutherElements},inplace=True,regex=True)
for i, col in enumerate(df.columns):
    df.iloc[:, i] = df.iloc[:, i].str.replace('"', '')
    df.iloc[:, i] = df.iloc[:, i].str.replace("'", '')
    df.iloc[:, i] = df.iloc[:, i].str.replace('amp', '')
    df.iloc[:, i] = df.iloc[:, i].str.replace('/a', '')

df

"""#Análisis de sentimientos"""

#Ejecutar la primera vez que se ejecuta el script.
!pip install googletrans==3.1.0a0

from googletrans import Translator
def Translate(originalList):
  translation=[]
  translator = Translator(service_urls=['translate.googleapis.com'])
  for i in range(len(originalList)):
    text=originalList[i]
    translatedText=translator.translate(text,dest='en')
    translation.append(translatedText.text)
  return translation

from textblob import TextBlob
#Para este código los comentarios deben ser traducidos a ingles.
comProcessadoList =df['comentarioProcesado'].tolist()
EnglishProccessedList=Translate(comProcessadoList)
#print(EnglishProccessedList)

#ejecutar una sola vez
!pip install emoji

def deEmojify(listOfComments):
  #Obtiene los emojis usados en los comentarios.
  emoList=[]
  regex=r'(\w+)(\w+)(\w+)'
  for i in range(len(listOfComments)):
    text=listOfComments[i]
    text = re.sub(r'(\w+)', '', text, flags=re.MULTILINE)
    text=re.sub(r'\(','',text)
    text=re.sub(r'\)','',text)
    text=re.sub(r' ','',text)
    emoList.append(text)
  return emoList
emoPrePross=df['comentarioProcesado'].values.tolist()
emoList=deEmojify(emoPrePross)
print(emoList)

"""Con la lista de emojis, falta asignarle valores para procesar el análisis de sentimientos, para mejorar este script se debe considerar los emojis escritos por el usuario de youtube"""

import emoji
emojiText=[]
emojis_detected=[]
for row in emoList:
  tempEmo=''
  emoRow=[]
  for e in row:
      tempEmo=tempEmo+','+ emoji.demojize(e,delimiters=("",""))
  emojiText.append(tempEmo)
  if tempEmo not in emojis_detected:
    emojis_detected.append(tempEmo)
emojis_detected

"""Polaridad y subjetividad"""

PolarityList=[]
SubjetivityList=[]
scoreList=[]
def getAnalysis(score):
  analysis='Negativo'
  if score == 0:
    analysis='Neutral'
  elif score > 0:
    analysis= 'Positivo'
  return analysis
for comment in EnglishProccessedList:

  analysis=TextBlob(comment)
  if analysis!="":
    sentimient=analysis.sentiment
    PolarityValue=sentimient.polarity
    SubjectivityValue=sentimient.subjectivity
    PolarityList.append(PolarityValue)
    SubjetivityList.append(SubjectivityValue)
    scoreList.append(getAnalysis(PolarityValue))
print(scoreList)

df['polaridad'] = PolarityList
df['subjetividad'] = SubjetivityList
df['puntuacion'] = scoreList
df

"""#Gráficas"""

df['polaridad'].value_counts()

df['puntuacion'].value_counts()
df['puntuacion'].replace(to_replace = np.nan, value ='Neutral', inplace=True)

df['puntuacion'].value_counts()

import matplotlib.pyplot as plt
graphLabels="Neutral","Positivo","Negativo"
graphColor=['#cbd6e4','#8be04e','#b30000']
plt.pie(df['puntuacion'].value_counts(),
        labels=graphLabels,
        colors=graphColor,
        autopct='%1.1f%%',shadow=True,startangle=90)
plt.title("Todos Aquí Son Id*otas | South Park ")
plt.axis('equal')
plt.show()

"""#WordCLoud"""

from wordcloud import WordCloud
text=" ".join(df.comentarioProcesado)
text

from wordcloud import WordCloud
import matplotlib.pyplot as plt

wordcloud=WordCloud(width=800, height=400, colormap='Blues',background_color='white',min_font_size=16).generate(text)

wordcloud=WordCloud(width=1024, height=800, colormap='Blues',min_font_size=14).generate(text)

plt.figure(figsize=(4,4),facecolor=None)
plt.imshow(wordcloud)
plt.axis("off")
plt.tight_layout(pad=0)
plt.show()

token=word_tokenize(text) #Transformo las palabras en una lista
fdist=FreqDist(token) #Cuenta la frecuencia de las palabras, crea un diccionario donde los key son las palabras, arroja luces sobre las palabras importantes
fdistl=fdist.most_common(9) #Genera lista de duplas ()
fdistl

fdist.plot(9)

"""#Conclusiones
1. A las personas les gusta que los protagonistas del show de south park sean niños
2. A los viewers les gusta la amistad , el cariño, la camaraderia de los protagonistas.
3. Se pueden observar los nombres de los personajes que fueron mejor recibidos son: Stan, Eric, Wendy, butters y de ultimo kayle.
4. Mayoritariamente los comentarios son positivos, indicando risas.
5. Existe un matiz ligeramente negativo en el video, que llegó a impactar a algunos viewers.
6. La forma en la que usan el humor para tocar temas profundos es uno de las cosas que le gustan al publico.
7. Los emojis deben ser procesados y estos indican tanto: sentimientos como emociones.

#Futuras Consideraciones:
1. Considerar los emojis obtenidos en la lista de emojis en el analisis de sentimientos.

2. Añadir Inteligencia artificial para que entienda el contexto de algunas palabras, para que se obtenga un mejor análisis. Por ejemplo  en español la palabra "amo" puede interpretarse de dos maneras dependiendo del contexto: amar, o dueña de algo. Este algoritmo por los momentos es incapaz de detectar el contexto de las oraciones
"""