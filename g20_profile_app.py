# -*- coding: utf-8 -*-


# Import needed libraries

import tweepy                   # Python wrapper around Twitter API
from PIL import Image
import requests
import json
import io
from flask import Flask, render_template, request, send_file, Response
from werkzeug.wsgi import FileWrapper


# Load Twitter API secrets from an external file
path = '/home/ykhoja'
secrets = json.loads(open(path + '/secrets.json').read())

consumer_key = secrets['consumer_key']
consumer_secret = secrets['consumer_secret']
access_token = secrets['access_token']
access_token_secret = secrets['access_token_secret']

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)


def get_profile_pic(user_id):
  """
  Returns the original size twitter profile pic for a specified user
  Input: a specific user's twitter handle
  Output: the original size profile pic
  """
  user = api.get_user(user_id)
  profile_pic_url = user._json['profile_image_url']
  # Get URL for original size image by dropping "_normal.jpg" from URL
  profile_pic_url = profile_pic_url.replace('_normal','')
  response = requests.get(profile_pic_url, stream=True).raw
  img = Image.open(response)
  return img


ribbon = Image.open(path + "/G20_ribbon_cropped.png")

def match_size(profile_pic, ribbon):
  w_pp, h_pp = profile_pic.size
  w_r , h_r  = ribbon.size

  if w_pp < w_r:
    factor = w_pp / w_r
    h_r = int(h_r * factor)
    ribbon = ribbon.resize((w_pp, h_r))

  else:
    factor = w_r / w_pp
    h_pp = int(h_pp * factor)
    profile_pic = profile_pic.resize((w_r, h_pp))

  return profile_pic, ribbon


def place_ribbon(profile_pic, ribbon):
  w_pp, h_pp = profile_pic.size
  w_r , h_r  = ribbon.size

  if h_pp < h_r:
    factor = w_pp / w_r
    h_r = int(h_r * factor)
    ribbon = ribbon.resize((w_pp, h_r))

  y = h_pp - h_r
  profile_pic.paste(ribbon, (0, y), mask=ribbon)

  return profile_pic


def create_g20_pic(user_id):
  profile_pic = get_profile_pic(user_id)
  ribbon = Image.open(path + "/G20_ribbon_cropped.png")
  new_pp, new_r = match_size(profile_pic, ribbon)
  pp_w_r = place_ribbon(new_pp, new_r)
  return pp_w_r


def serve_pil_image(pil_img):
    img_io = io.BytesIO()
    pil_img.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    w = FileWrapper(img_io)
    return Response(w, mimetype='image/jpeg', direct_passthrough=True)
    # return send_file(FileWrapper(img_io), mimetype='image/jpeg')


app = Flask(__name__, template_folder=path + '/g20_profile_pic_maker/templates/')

@app.route("/")
def form():
    return render_template('form.html')

@app.route('/', methods=['POST', 'GET'])
def my_form_post():
    text = request.form['text']
    user_id = text.lower()
    img = create_g20_pic(user_id)
    return serve_pil_image(img)
