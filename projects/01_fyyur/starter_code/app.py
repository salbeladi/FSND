#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import date
import phonenumbers
from wtforms import ValidationError

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)    
    phone = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    image_link = db.Column(db.String(500))

    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
      return f'<Venue {self.id} {self.name}>'
    
class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)
 
app.jinja_env.filters['datetime'] = format_datetime

# validates user phone numbers
def phone_validation(num):
    parsed = phonenumbers.parse(num, "US")
    if not phonenumbers.is_valid_number(parsed):
        raise ValidationError('Must enter a valid phone number.')
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#
@app.route('/')
def index():
  return render_template('pages/home.html')
#----------------------------------------------------------------------------#
#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  
  # data will hold all venues returned
  data = []

  # Collect all the venues
  venues = Venue.query.all()

  # a set to store unique combination of city and state
  venue_locations = set()

  # store all combination into the set venue_locations
  for location in venues:
    venue_locations.add((location.city, location.state))

  # store all location inside the data object
  for location in venue_locations:
    data.append({
      "city": location[0],
      "state": location[1],
      "venues": []
    })

  # find the upcoming shows for each venue, store venues in the data object
  for venue in venues:
    # get all shows for the current venue
    shows = Show.query.filter_by(venue_id = venue.id).all()

    # calculate number of upcoming shows
    total_upcoming_shows = 0
    for show in shows:
      if show.start_time > datetime.now():
        total_upcoming_shows +=1
    # storing venue data into the specific location
    for location in data:
      if venue.city == location["city"] and venue.state == location["state"]:
        location["venues"].append({
          "id": venue.id,
          "name": venue.name,
          "upcoming_shows": total_upcoming_shows
        })

# pass data to the template
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  
  # search term entered by user
  search_term = request.form.get('search_term', '')

  # find venues with partial string search, case-insensitive
  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()

  # response stores data result
  response = []

  # add how many results matches the search term
  response = {
    "count": len(venues),
    "data": []
  }
  # iterating each venue and add it to the response object
  for venue in venues:
     response["data"].append({
       "id": venue.id,
       "name": venue.name
    })
 
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # data members to store the data of upcoming and past shows
  upcoming_shows = []
  past_shows = []

  # retrieve the venue using id 
  venue = Venue.query.filter_by(id = venue_id ).first()

  # retrieve all shows for this venue
  shows = Show.query.filter_by(venue_id = venue_id).all()
  # filter shows based on their date 
  for show in shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id = show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id = show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time)) 
      })
    elif show.start_time < datetime.now():
      past_shows.append({
          "artist_id": show.artist_id,
          "artist_name": Artist.query.filter_by(id = show.artist_id).first().name,
          "artist_image_link": Artist.query.filter_by(id = show.artist_id).first().image_link,
          "start_time": format_datetime(str(show.start_time)) 
        })
  # data is the object will store the data of the venue and it's shows
  data = {
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # insert form data as a new Venue record in the db
  # modify data to be the data object returned from db insertion
  try:
    # load form data from the user input after submission
    form = VenueForm()
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    phone_validation(phone)
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website = form.website.data
    image_link = form.image_link.data
    seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    seeking_description = form.seeking_description.data
    # create new Venue
    venue = Venue(name = name, city = city, state = state, address = address,
                  phone = phone, genres = genres, facebook_link = facebook_link,
                  website = website, image_link = image_link,
                  seeking_talent = seeking_talent,seeking_description = seeking_description)
    # add new venue to session and commit to database
    db.session.add(venue)
    # commit the session
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' is successfully listed!')
  # incase of an error, flash and error
  except ValidationError as e:
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed. ' + str(e))

  except:
    # catches all other exceptions
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')

  finally:
    # always close the session
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    # retrieve data of the venue
    venue = Venue.query.filter_by(id = venue_id).first()
    # store name of venue to display incase an error being flashed
    name = venue.name
    # delete this object from databae
    db.session.delete(venue)
    db.session.commit()
    # when deleted successfully
    flash('Venue ' + name + ' was successfully deleted.')

  except:
    db.session.rollback()
    flash('An error occurred.! The venue: ( '+ name + ' ) could not be deleted')
  
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # real data returned from querying the database
  data=[]
  # retrieve all artists data from db
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # search on artists with partial string search, case-insensitive

  # search term entered by user
  search_term = request.form.get('search_term', '')

  # find artists with partial string search, case-insensitive
  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

  # response stores all data result
  response = []

  # add how many results matches the search term
  response = {
    "count": len(artists),
    "data": []
  }

  # iterating each artist and add it to the response object
  for artist in artists:
     response["data"].append({
       "id": artist.id,
       "name": artist.name
    })
 
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # data members to store the data of upcoming and past shows
  upcoming_shows = []
  past_shows = []

  # retrieve the artist data from database using id 
  artist = Artist.query.filter_by(id = artist_id ).first()

  # get all shows for this artist
  shows = Show.query.filter_by(artist_id = artist_id).all()

  # filter shows as past and upcoming shows
  for show in shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": Venue.query.filter_by(id = show.venue_id).first().name,
        "venue_image_link": Venue.query.filter_by(id = show.venue_id).first().image_link,
        "start_time": format_datetime(str(show.start_time)) 
      })
    elif show.start_time < datetime.now():
      past_shows.append({
         "venue_id": show.venue_id,
        "venue_name": Venue.query.filter_by(id = show.venue_id).first().name,
        "venue_image_link": Venue.query.filter_by(id = show.venue_id).first().image_link,
        "start_time": format_datetime(str(show.start_time)) 
        })
  # object to store the artist data along with list of upcoming and past shows
  data = {
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows": upcoming_shows,
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_artist.html', artist=data)
  # delete artist
@app.route('/artists/<artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
  try:
    # retrieve data of the artist
    artist = Artist.query.filter_by(id = artist_id).first()
    # store name of artist to display incase an error being flashed
    name = artist.name
    # delete this object from databae
    db.session.delete(artist)
    db.session.commit()
    # when deleted successfully
    flash('Artist ' + name + ' was successfully deleted.')

  except:
    db.session.rollback()
    flash('An error occurred.! The artist: ( '+ name + ' ) could not be deleted')
  
  finally:
    db.session.close()

  return render_template('pages/home.html')
#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):

  # retrieve data of artist from db using id
  artist = Artist.query.filter_by(id = artist_id).first()

  # create form and object to store data 
  form = ArtistForm()
  artist={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link
  }
  # pass data to the form elements
  form.name.process_data(artist['name'])
  form.city.process_data(artist['city'])
  form.state.process_data(artist['state'])
  form.phone.process_data(artist['phone'])
  form.genres.process_data(artist['genres'])
  form.seeking_venue.process_data(artist['seeking_venue'])
  form.facebook_link.process_data(artist['facebook_link'])
  form.website.process_data(artist['website'])
  form.image_link.process_data(artist['image_link'])

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    form = ArtistForm()

    # get the artist data using id
    artist = Artist.query.filter_by(id = artist_id).first()

    # load data from user input on form submit
    artist.name = form.name.data
    artist.city = form.city.data
    artist.state = form.state.data
    artist.phone = form.phone.data
    phone_validation(artist.phone)
    artist.facebook_link = form.facebook_link.data
    artist.image_link = form.image_link.data
    artist.website = form.website.data
    artist.seeking_venue = True if form.seeking_venue.data == 'Yes' else False
    artist.genres = form.genres.data

    # commit the changes
    db.session.commit()

    flash('Artist ' + request.form['name'] + ' was successfully updated!')
  except ValidationError as e:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed. ' + str(e))
  except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
      db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):  

  # retrieve data of a venue to edit
  venue = Venue.query.filter_by(id = venue_id).first()

  #form and object hold the data retrieved from db
  form = VenueForm()
  venue={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link
  }
  # pass data to the form objects
  form.name.process_data(venue['name'])
  form.address.process_data(venue['address'])
  form.city.process_data(venue['city'])
  form.state.process_data(venue['state'])
  form.phone.process_data(venue['phone'])
  form.genres.process_data(venue['genres'])
  form.seeking_talent.process_data(venue['seeking_talent'])
  form.seeking_description.process_data(venue['seeking_description'])
  form.facebook_link.process_data(venue['facebook_link'])
  form.website.process_data(venue['website'])
  form.image_link.process_data(venue['image_link'])
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    form = VenueForm()

    # get the current artist by id
    venue = Venue.query.filter_by(id=venue_id).first()

    # load new edited data from venue edit form
    venue.name = form.name.data
    venue.genres = form.genres.data
    venue.city = form.city.data
    venue.state = form.state.data
    venue.address = form.address.data
    venue.phone = form.phone.data
    phone_validation(venue.phone)
    venue.facebook_link = form.facebook_link.data
    venue.website = form.website.data
    venue.image_link = form.image_link.data
    venue.seeking_talent = True if form.seeking_talent.data == 'Yes' else False
    venue.seeking_description = form.seeking_description.data

    # commit the changes
    db.session.commit()

    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except ValidationError as e:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed. ' + str(e))
  except:
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be updated.')
  finally:
      db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

  # insert form data as a new Venue record in the db

  try:
    # load form data from the user input after submission
    form = ArtistForm()
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    phone_validation(phone)
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website = form.website.data
    image_link = form.image_link.data
    seeking_venue = True if form.seeking_venue.data == 'Yes' else False

    # create new Artist object
    artist = Artist(name = name, city = city, state = state,
                  phone = phone, genres = genres, facebook_link = facebook_link,
                  website = website, image_link = image_link,seeking_venue = seeking_venue)

    # add new venue to session and commit to the database
    db.session.add(artist)
    db.session.commit()

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  
  except ValidationError as e:
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed. ' + str(e))

  except:
    # catches all other exceptions
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')

  finally:
    # always close the session
    db.session.close()
  return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # retrieve all shows from database
  shows = Show.query.all()

  data = []
  # iterate the shows
  for show in shows:
    # get the venue hosting this show 
    venue = Venue.query.filter_by(id = show.venue_id).first()
    # get artist of this show data
    artist = Artist.query.filter_by(id = show.artist_id).first()
    # store all data into data object
    data.append({
          "venue_id": show.venue_id,
          "venue_name": venue.name,
          "artist_id": show.artist_id,
          "artist_name": artist.name,
          "artist_image_link": artist.image_link,
          "start_time": format_datetime(str(show.start_time))
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # insert form data as a new Show record in the db, instead

  try:
    # load form data from the user input after submission
    form = ShowForm()
    # store data received from user
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    # create new show object with user input
    show = Show(artist_id = artist_id, venue_id = venue_id, start_time = start_time)

    # add new show to session and commit it to the database
    db.session.add(show)
    db.session.commit()

    # flash success when it's been committed
    flash('Show is successfully listed!')

  except:
    # catches any exceptions
    db.session.rollback()
    flash('An error occurred. Show could not be listed.')

  finally:
    # close the session
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
