#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import *
from sqlalchemy import case, select, func, update, delete
from datetime import datetime
from werkzeug.datastructures import MultiDict
from models import db
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# TODO: connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI']=SQLALCHEMY_DATABASE_URI
db.init_app(app)

migrate = Migrate(app, db)

with app.app_context():
   db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
     date = dateutil.parser.parse(value)
  else:
     date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venues = venue.query.all()
  data = {}

  for venueData in venues:
     location_key = f"{venueData.city}, {venueData.state}"
     if location_key not in data:
        data[location_key] = {
           "city": venueData.city,
           "state": venueData.state,
           "venues": []
        }
     data[location_key]["venues"].append({
         "id": venueData.id,
         "name": venueData.name
     })
  
  result = list(data.values())

  return render_template('pages/venues.html', areas=result);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  key_word = request.form['search_term']
  query = db.session.query(venue).filter(venue.name.ilike(f'%{key_word}%')).all()
  data = []

  for venue_data in query:
      shows = db.session.query(show.id, show.start_time).filter(
        show.venue_id == venue_data.id,
        show.start_time > func.now()
      ).all()

      venue_data_temp = {
          "id": venue_data.id,
          "name": venue_data.name,
          "num_upcoming_shows": len(shows)
      }
      data.append(venue_data_temp)

  response={
    "count": len(query),
    "data": data
  }

  return render_template('pages/search_venues.html', results=response, search_term=key_word)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue_data = venue.query.get(venue_id)

  # mapping past shows and upcoming shows
  query = (
     db.session.query(
        show.artist_id,
        show.start_time,
        case(
           (show.start_time < func.now(), True),
           else_=False
        ).label('is_past')
     )
     .filter(show.venue_id == venue_id)
  )
  shows = query.all()
  past_shows = []
  upcoming_shows = []

  for showData in shows:
    artistData = artist.query.get(showData.artist_id)
    show_temp = {
        "artist_id": artistData.id,
        "artist_name": artistData.name,
        "artist_image_link": artistData.image_link,
        "start_time": showData.start_time
    }
    if showData.is_past:
        past_shows.append(show_temp)
    else:
        upcoming_shows.append(show_temp)

  #final response
  response = {
    "id": venue_data.id,
    "name": venue_data.name,
    "genres": json.loads(venue_data.genres),
    "address": venue_data.address,
    "city": venue_data.city,
    "state": venue_data.state,
    "phone": venue_data.phone,
    "website": venue_data.website_link,
    "facebook_link": venue_data.facebook_link,
    "seeking_talent": venue_data.seeking_talent,
    "seeking_description": venue_data.seeking_description,
    "image_link": venue_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=response)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)

  if form.validate_on_submit():
    try:
      new_venue = venue(
        name = form.name.data,
        city = form.city.data,
        state = form.state.data,
        address = form.address.data,
        phone = form.phone.data,
        genres = json.dumps(form.genres.data),
        facebook_link = form.facebook_link.data,
        image_link = form.image_link.data,
        website_link = form.website_link.data,
        seeking_talent = form.seeking_talent.data,
        seeking_description = form.seeking_description.data
      )
      
      db.session.add(new_venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')
      return render_template('pages/home.html')
    except Exception as e:
      db.session.rollback()
      # TODO: on unsuccessful db insert, flash an error instead.
      # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred!', 'error')
      print(f'Error: {e}')
    finally:
      db.session.close()
  
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  shows = db.session.query(show).filter(show.venue_id == venue_id).all()

  if len(shows) != 0:
     flash("You can't delete this venue because it is using", "error")
     return render_template('pages/home.html')

  try:
    db.session.execute(delete(venue).where(venue.id == venue_id))
    db.session.commit()
    flash("Venue deleted successfully!")
  except Exception as e:
    db.session.rollback()
    flash(f"An error occurred: {e}")
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data=db.session.query(artist.id, artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  key_word = request.form['search_term']

  query = db.session.query(artist).filter(artist.name.ilike(f'%{key_word}%')).all()
  data = []

  for show_data in query:
    shows = db.session.query(show.id, show.start_time).filter(
      show.artist_id == show_data.id,
      show.start_time > func.now()
    ).all()

    show_data_temp = {
        "id": show_data.id,
        "name": show_data.name,
        "num_upcoming_shows": len(shows)
    }
    data.append(show_data_temp)

  response={
    "count": len(query),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=key_word)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  artist_data = artist.query.get(artist_id)

  # mapping past shows and upcoming shows
  query = (
     db.session.query(
        show.venue_id,
        show.start_time,
        case(
           (show.start_time < func.now(), True),
           else_=False
        ).label('is_past')
     ).filter(show.artist_id == artist_id)
  )

  shows = query.all()
  past_shows = []
  upcoming_shows = []

  for show_data in shows:
     venue_data = venue.query.get(show_data.venue_id)
     show_temp = {
      "venue_id": venue_data.id,
      "venue_name": venue_data.name,
      "venue_image_link": venue_data.image_link,
      "start_time": show_data.start_time
     }

     if show_data.is_past:
        past_shows.append(show_temp)
     else:
        upcoming_shows.append(show_temp)

  #final response
  response = {
    "id": artist_data.id,
    "name": artist_data.name,
    "genres": json.loads(artist_data.genres),
    "city": artist_data.city,
    "state": artist_data.state,
    "phone": artist_data.phone,
    "website": artist_data.website_link,
    "facebook_link": artist_data.facebook_link,
    "seeking_venue": artist_data.seeking_venue,
    "seeking_description": artist_data.seeking_description,
    "image_link": artist_data.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=response)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  data = artist.query.get(artist_id)
  data_temp = {
     'name': data.name,
     'city': data.city,
     'state': data.state,
     'phone': data.phone,
     'image_link': data.image_link,
     'genres': data.genres,
     'facebook_link': data.facebook_link,
     'website_link': data.website_link,
     'seeking_venue': data.seeking_venue,
     'seeking_description': data.seeking_description
  }

  form = ArtistForm(formdata=MultiDict(data_temp))

  form.genres.data = json.loads(data.genres)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=data, artist_id=artist_id)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  data = artist.query.get(artist_id)

  if form.validate_on_submit():
    try:
      data.name = form.name.data
      data.city = form.city.data
      data.state = form.state.data
      data.phone = form.phone.data
      data.genres = json.dumps(form.genres.data)
      data.image_link = form.image_link.data
      data.facebook_link = form.facebook_link.data
      data.website_link = form.website_link.data
      data.seeking_venue = form.seeking_venue.data
      data.seeking_description = form.seeking_description.data
      
      db.session.commit()
      flash('update artist '+ form.name.data +' was successfully')
      return redirect(url_for('show_artist', artist_id=artist_id))
    except Exception as e:
      db.session.rollback()
      flash('An error occurred!', 'error')
      print(f'Error: {e}')
    finally:
      db.session.close()

  return render_template('forms/edit_artist.html', form=form, artist=data, artist_id=artist_id)

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  data = venue.query.get(venue_id)
  data_temp = {
    'name': data.name,
    'city': data.city,
    'state': data.state,
    'address': data.address,
    'phone': data.phone,
    'genres': data.genres,
    'facebook_link': data.facebook_link,
    'image_link': data.image_link,
    'website_link': data.website_link,
    'seeking_talent': data.seeking_talent,
    'seeking_description': data.seeking_description
  }
  form = VenueForm(formdata=MultiDict(data_temp))
  
  form.genres.data = json.loads(data.genres)

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=data, venue_id=venue_id)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  data = venue.query.get(venue_id)

  if form.validate_on_submit():
    try:
      data.name = form.name.data
      data.city = form.city.data
      data.state = form.state.data
      data.address = form.address.data
      data.phone = form.phone.data
      data.genres = json.dumps(form.genres.data)
      data.image_link = form.image_link.data
      data.facebook_link = form.facebook_link.data
      data.website_link = form.website_link.data
      data.seeking_talent = form.seeking_talent.data
      data.seeking_description = form.seeking_description.data
      
      db.session.commit()
      flash('update venue '+ form.name.data +' was successfully')
      return redirect(url_for('show_venue', venue_id=venue_id))
    except Exception as e:
      db.session.rollback()
      flash('An error occurred!', 'error')
      print(f'Error: {e}')
    finally:
      db.session.close()

  return render_template('forms/edit_venue.html', form=form, venue=data, venue_id=venue_id)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)

  if form.validate_on_submit():
    try:
      new_artist = artist(
          name = form.name.data,
          city = form.city.data,
          state = form.state.data,
          phone = form.phone.data,
          genres = json.dumps(form.genres.data),
          image_link = form.image_link.data,
          facebook_link = form.facebook_link.data,
          website_link = form.website_link.data,
          seeking_venue = form.seeking_venue.data,
          seeking_description = form.seeking_description.data
      )
      db.session.add(new_artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
      return render_template('pages/home.html')
    except Exception as e:
      db.session.rollback()
      flash('An error occurred. Artist ' + form.name.data + ' could not be listed.', 'error')
      print(f'Error: {e}')
    finally:
      db.session.close()
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data = []
  query = db.session.query(
     venue.id.label('venue_id'),
     venue.name.label('venue_name'),
     artist.id.label('artist_id'),
     artist.name.label('artist_name'),
     artist.image_link.label('artist_image_link'),
     show.start_time
  ).join(venue, venue.id == show.venue_id).join(artist, artist.id == show.artist_id)

  shows_data = query.all()

  for show_data in shows_data:
     data_temp = {
        "venue_id": show_data.venue_id,
        "venue_name": show_data.venue_name,
        "artist_id": show_data.artist_id,
        "artist_name": show_data.artist_name,
        "artist_image_link": show_data.artist_image_link,
        "start_time": show_data.start_time
     }
     data.append(data_temp)

  print(data)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create', methods=['GET'])
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)

  if form.validate_on_submit():
    try:
      new_show = show(
        artist_id = form.artist_id.data,
        venue_id = form.venue_id.data,
        start_time = form.start_time.data
      )

      db.session.add(new_show)
      db.session.commit()
      flash('Show was successfully listed!', 'success')
      return render_template('pages/home.html')
    except Exception as e:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.', 'error')
      print(f'Error: {e}')
    finally:
      db.session.close()
    # on successful db insert, flash success
  
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('forms/new_show.html', form=form)

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
