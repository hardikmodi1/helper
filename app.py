from flask import Flask,render_template,request,redirect,jsonify
import sys
import os
sys.path.append(os.path.abspath('./model'))
from load import *
from keras.preprocessing import image
import numpy as np
from keras import backend as K
import tensorflow as tf
from keras.models import load_model
from bs4 import BeautifulSoup
import requests
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app=Flask(__name__)

UPLOAD_FOLDER = os.path.basename('images')
MODEL_FOLDER = os.path.basename('model')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MONGO_DBNAME']='hackathon'
app.config['MONGO_URI']='mongodb://hardik:hardik97122@ds251223.mlab.com:51223/hackathon'

mongo=PyMongo(app)

def preprocess_input(x, dim_ordering='default'):
    if dim_ordering == 'default':
        dim_ordering = K.image_dim_ordering()
    assert dim_ordering in {'tf', 'th'}

    if dim_ordering == 'th':
        x[:, 0, :, :] -= 103.939
        x[:, 1, :, :] -= 116.779
        x[:, 2, :, :] -= 123.68
        # 'RGB'->'BGR'
        x = x[:, ::-1, :, :]
    else:
        x[:, :, :, 0] -= 103.939
        x[:, :, :, 1] -= 116.779
        x[:, :, :, 2] -= 123.68
        # 'RGB'->'BGR'
        x = x[:, :, :, ::-1]
    return x


global graph,model,labels,typeOf
graph = tf.get_default_graph()
model_path=os.path.join(MODEL_FOLDER, 'model.h5')
model = load_model(model_path)
labels=['Tomato+Septoria+leaf+spot',
 'Tomato+Bacterial+spot',
 'Tomato+Yellow+Leaf+Curl+Virus',
 'Tomato+healthy',
 'Tomato+Target_Spot',
 'Tomato+Early+blight',
 'Tomato+Late+blight',
 'Tomato+mosaic+virus',
 'Tomato+Spider+mites',
 'Tomato+Leaf+Mold',
 'Potato+healthy',
 'Raspberry+healthy',
 'Strawberry+healthy',
 'Soybean+healthy',
 'Squash+Powdery+mildew',
 'Potato+Late+blight',
 'Pepper+bell+healthy',
 'Strawberry+Leaf+scorch',
 'Pepper+bell+Bacterial+spot',
 'Potato+Early+blight',
 'Grape+healthy',
 'Peach+Bacterial+spot',
 'Corn+maize+healthy',
 'Corn+maize+Northern+Leaf+Blight',
 'Grape+Leaf+blight+Isariopsis+Leaf+Spot',
 'Peach+healthy',
 'Grape+Black+rot',
 'Orange+Citrus+greening',
 'Grape+Esca+Black+Measles',
 'Corn+maize+Common+rust',
 'Blueberry+healthy',
 'Apple+Black+rot',
 'Apple+healthy',
 'background',
 'Cherry+including+sour+healthy',
 'Corn+maize+Cercospora+leaf+spot',
 'Apple+scab',
 'Apple+Cedar+rust',
 'Cherry+including+sour+Powdery+mildew']


@app.route("/home")
def home():
	return render_template('home.html')


@app.route("/news")
def news():
	query="https://economictimes.indiatimes.com/news/economy/agriculture"
	r=requests.get(query)
	soup = BeautifulSoup(r.text, 'html.parser')
	sub_heading = soup.find_all('div',{"class":"eachStory"})
	img_link_arr=[]
	headline=[]
	link=[]
	para=[]
	for i in range(0,len(sub_heading)):
		img_link_arr.append(sub_heading[i].a.span.img['data-original'])
		headline.append(sub_heading[i].h3.a.meta['content'])
		link.append("https://economictimes.indiatimes.com"+sub_heading[i].h3.a['href'])
		para.append(sub_heading[i].p.get_text())
	return render_template(
		'news.html',
		img_link_arr=img_link_arr,
		headline=headline,
		link=link,
		para=para
	)

@app.route("/price")
def price():
	count=1
	response=requests.get("https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key=579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b&format=json&offset=0&limit=10")
	response=response.json()['records']
	# print(response)
	return render_template('price.html',responses=response,count=count)

@app.route("/price/<url>")
def pricenext(url):
	# print(count)
	count=int(url)
	print(count)
	print(type(count))
	response=requests.get("https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070?api-key=579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b&format=json&offset="+str(((count-1)*10))+"&limit=10")
	response=response.json()['records']
	# print(response)
	return render_template('price.html',responses=response,count=count)


@app.route("/")
def lend():
	return render_template('index.html')

@app.route("/question/<url>", methods=['GET'])
def showspecificquestion(url):
	print("url of the page is",type(url))
	# related_questions = mongo.db.questions.find_one({"_id":url})
	specific_question=[i for i in mongo.db.questions.find({"_id": ObjectId(url)})]
	question=specific_question[0]['question']
	questionId=specific_question[0]['_id']
	typeOf=specific_question[0]['type']
	answers=mongo.db.questions.find({"questionId": url})
	return render_template('onequestion.html',question=question,questionId=questionId,answers=answers)

@app.route("/showall/<url>", methods=['GET'])
def showspecific(url):
	print("url of the page is",url)
	related_questions = mongo.db.questions.find({"type": url})
	return render_template('allquestions.html',related_questions=related_questions,specific=True)

@app.route("/showall", methods=['GET'])
def showall():
	all_questions = mongo.db.questions.find({})
	related_questions=[]
	for r in all_questions:
		if r['questionId']==0:
			related_questions.append(r)
	return render_template('allquestions.html',related_questions=related_questions,specific=False)

@app.route("/submitask", methods=['POST'])
def submitask():
	question=mongo.db.questions
	objToInsert={
		'question': request.form['question'],
		'type': request.form['dname'],
		'questionId':0
	}
	question.insert(objToInsert)
	print(request.form['question'])
	print(request.form['dname'])
	return redirect('/showall/'+request.form['dname'])

@app.route("/submitanswer", methods=['POST'])
def submitanswer():
	question=mongo.db.questions
	objToInsert={
		'question': request.form['answer'],
		'questionId': request.form['questionId']
	}
	question.insert(objToInsert)
	print(request.form['answer'])
	print(request.form['questionId'])
	return redirect('/question/'+request.form['questionId'])

@app.route("/ask", methods=['GET'])
def ask():
	return render_template('ask.html')

@app.route("/predict",methods=['POST'])
def predict():
	

	file = request.files['image']
	f = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)

	# add your custom code to check that the uploaded file is a valid image and not a malicious file (out-of-scope for this post)
	file.save(f)
	print("saved")
	img_path=f
	img=image.load_img(img_path,target_size=(224,224))
	# imag=mpimg.imread(img_path)
	# imgplot = plt.imshow(imag)
	# plt.show()
	x=image.img_to_array(img)
	x=np.expand_dims(x,axis=0)
	x=preprocess_input(x)
	prediction=[]
	with graph.as_default():
		out=model.predict(x)
		print(out)
		prediction.append(labels[np.argmax(out)])
		print(labels[np.argmax(out)])
	# google_search="https://www.google.com/search?q=Apple+Scab&source=lnms&tbm=nws"
	youtube_search="https://www.youtube.com/results?search_query=how+to+cure+"+labels[np.argmax(out)]
	google_search='https://www.google.co.in/search?q="+labels[np.argmax(out)]+"&oq="+labels[np.argmax(out)]+"&gs_l=serp.12..0i71l8.0.0.0.6391.0.0.0.0.0.0.0.0..0.0....0...1c..64.serp..0.0.0.UiQhpfaBsuU'
	r=requests.get(google_search)
	r1=requests.get(youtube_search)
	soup=BeautifulSoup(r.text,'html.parser')
	soup1=BeautifulSoup(r1.text,'html.parser')
	headline=soup.find_all('span',{"class":"st"})
	link=soup.find_all('cite')
	# youtube_text=soup1.find_all('h3')
	# youtube_link=soup1.find_all('cite')
	link_array=[]
	text_array=[]
	vid_link_arr=[]
	vid_text_arr=[]
	vid_thumb_arr=[]
	count=0
	div=[d for d in soup1.find_all('div') if d.has_attr('class') and 'yt-lockup-dismissable' in d['class']]
	for i in div:
		if count >= 5:
			break
		img0=i.find_all('img')[0]
		imgL=img0['src'] if not img0.has_attr('data-thumb') else img0['data-thumb']
		a=[x for x in i.find_all('a') if x.has_attr('title')]
		a0=[x for x in i.find_all('a') if x.has_attr('title')][0]
		vid_text_arr.append(a0['title'])
		vid_link_arr.append("https://www.youtube.com"+a[0]['href'])
		vid_thumb_arr.append(imgL)
		count=count+1
	print(vid_link_arr)
	print(vid_text_arr)
	print(vid_thumb_arr)
	count=0
	for h in link:
		if count >= 5:
			break
		# print('links  are',h.get_text())
		if h.get_text() not in link_array:
			if "https" not in h.get_text():
				link_array.append("https://"+h.get_text())
			else:
				link_array.append(h.get_text())
		count=count+1
	print(link_array)
	count=0
	for h in headline:
		if count >= 5:
			break
		# print('links  are',h.get_text())
		if h.get_text() not in text_array:
			text_array.append(h.get_text())
		count=count+1
	print(text_array)
	# return 'jsonify(prediction)'
	context={
		
	}
	prediction="apple_scab"
	if "healthy" in prediction:
		show=False
	else:
		show=True
	return render_template(
		'result.html',
	    link_array=link_array,
		text_array=text_array,
		vid_link_arr=vid_link_arr,
		vid_text_arr=vid_text_arr,
		vid_thumb_arr=vid_thumb_arr,
		prediction=labels[np.argmax(out)],
		show=show

	)


@app.route("/testing",methods=['POST'])
def testing():
	return "hello"
	
	# with graph.as_default():
	# 	out=model.predict(x)
	# 	print(out)
	# 	print(labels[np.argmax(out)])
	return render_template('home.html')

if __name__=="__main__":
	app.run()