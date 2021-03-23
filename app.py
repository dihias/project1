#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import (
    Flask, 
    render_template, 
    request, 
    Response, 
    flash, 
    redirect, 
    url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from models import db, Venue, Artist, Show  
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
#because db is in models.py
db.init_app(app)

# TODO: connect to a local postgresql database
migration = Migrate(app, db)
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
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  city_state = db.session.query(Venue.city,Venue.state).group_by(Venue.state,Venue.city).all()
  data = []
  for cs in city_state:
    venues = db.session.query(Venue.id,Venue.name).filter(Venue.city==cs[0],Venue.state==cs[1]).all()
    data.append({
        "city": cs[0],
        "state": cs[1],
        "venues": []
    })
    for venue in venues:
      data[-1]["venues"].append({
              "id": venue[0],
              "name": venue[1],
              
      })

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():

  results = Venue.query.filter(Venue.name.ilike('%{}%'.format(request.form['search_term']))).all()
  response={
    "count": len(results),
    "data": []
    }
  for venue in results:
    response["data"].append({
        "id": venue.id,
        "name": venue.name,
        
      })
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  past_shows = []
  upcoming_shows = []
  for show in venue.shows:
      if show.start_time <= datetime.now():
          past_shows.append({
              'artist_id': show.artist_id,
              'artist_name': show.artists.name,
              "artist_image_link": show.artists.image_link,
              'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
          })
      else:
          upcoming_shows.append({
              'artist_id': show.artist_id,
              'artist_name': show.artists.name,
              "artist_image_link": show.artists.image_link,
              'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
          })

  data={
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
    'past_shows': past_shows,
    'upcoming_shows': upcoming_shows,
    'past_shows_count': len(past_shows),
    'upcoming_shows_count': len(upcoming_shows)
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  
  form = VenueForm(request.form)
  new_venue = Venue()
  new_venue.name = form.name.data,
  new_venue.city = form.city.data
  new_venue.state = form.state.data
  new_venue.address = form.address.data
  new_venue.phone = form.phone.data
  new_venue.facebook_link = form.facebook_link.data
  new_venue.genres = form.genres.data

  new_venue.image_link = form.image_link.data
  new_venue.website = form.website.data
  new_venue.seeking_description = form.seeking_description.data
  new_venue.seeking_talent = form.seeking_talent.data
  try:
    db.session.add(new_venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  delete Venue
#  ----------------------------------------------------------------
@app.route('/venues/delete', methods=['POST'])
def delete_venue():

  venue_id = request.form.get('venue_id')
  deleted_venue = Venue.query.get(venue_id)
  venueName = deleted_venue.name
  try:
    db.session.delete(deleted_venue)
    db.session.commit()
    flash('Venue ' + venueName + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('please try again. Venue ' + venueName + ' could not be deleted.')
  finally:
    db.session.close()

  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  
  data= Artist.query.with_entities(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():

  results = Artist.query.filter(Artist.name.ilike('%{}%'.format(request.form['search_term']))).all()

  response={
    "count": len(results),
    "data": []
  }
  for artist in results:
    response['data'].append({
      "id": artist.id,
      "name": artist.name,
      })
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

  artist = Artist.query.get(artist_id)
  shows = artist.shows
  past_shows = []
  upcoming_shows = []
    
  for show in artist.shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
          'venue_id': show.venue_id,
          'venue_name': show.venues.name,
          "venue_image_link": show.venues.image_link,
          'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        })
    else:
      past_shows.append({
          'artist_id': show.artist_id,
          'artist_name': show.artists.name,
          "artist_image_link": show.artists.image_link,
          'start_time': show.start_time.strftime("%m/%d/%Y, %H:%M")
        })
    

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
    "seeking_description":artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }

  return render_template('pages/show_artist.html', artist=data)

#  delete artist
#  ----------------------------------------------------------------
@app.route('/artists/delete', methods=['POST'])
def delete_artist():
  artist_id = request.form.get('artist_id')
  deleted_artist = Artist.query.get(artist_id)
  artistName = deleted_artist.name
  try:
    db.session.delete(deleted_artist)
    db.session.commit()
    flash('Artist ' + artistName + ' was successfully deleted!')
  except:
    db.session.rollback()
    flash('please try again. Venue ' + artistName + ' could not be deleted.')
  finally:
    db.session.close()
  
  return render_template('pages/home.html')
#  Update
#  ----------------------------------------------------------------
@app.route('/artists/edit', methods=['GET'])
def edit_artist():
  form = ArtistForm()
  artist_id = request.args.get('artist_id')
  artist = Artist.query.get(artist_id)
  artist_info={
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
  
  return render_template('forms/edit_artist.html', form=form, artist=artist_info)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  artist = Artist.query.get(artist_id)
  artist.name = request.form['name']
  artist.city = request.form['city']
  artist.state = request.form['state']
  artist.phone = request.form['phone']
  artist.facebook_link = request.form['facebook_link']
  artist.genres = request.form['genres']
  #artist.image_link = request.form['image_link']
  #artist.website = request.form['website']
  try:
    db.session.commit()
    flash("Artist {} is updated successfully".format(artist.name))
  except:
    db.session.rollback()
    flash("Artist {} isn't updated successfully".format(artist.name))
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/edit', methods=['GET'])
def edit_venue():
  venue_id = request.args.get('venue_id')
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  venue_info={
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
 
  return render_template('forms/edit_venue.html', form=form, venue=venue_info)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  venue = Venue.query.get(venue_id)
  venue.name = request.form['name']
  venue.city = request.form['city']
  venue.state = request.form['state']
  venue.address = request.form['address']
  venue.phone = request.form['phone']
  venue.facebook_link = request.form['facebook_link']
  venue.genres = request.form['genres']
  #venue.image_link = request.form['image_link']
  #venue.website = request.form['website']
  try:
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('An error occurred. Venue ' + new_venue.name + ' could not be updated.')
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)
  new_artist = Artist()
  new_artist.name = form.name.data
  new_artist.city = form.city.data
  new_artist.state = form.state.data
  new_artist.genres = form.genres.data
  new_artist.phone = form.phone.data
  new_artist.facebook_link = form.facebook_link.data
  new_artist.image_link = form.image_link.data
  new_artist.website = form.website.data
  new_artist.seeking_description = form.seeking_description.data
  new_artist.seeking_talent = form.seeking_talent.data
  try:
    db.session.add(new_artist)
    db.session.commit()
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + new_artist.name + ' could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

  shows_list = Show.query.all()


  data = []
  for show in shows_list:
    
    data.append({
    "venue_id": show.venue_id,
    "venue_name": show.venue.name,
    "artist_id": show.artist_id,
    "artist_name": show.artist.name,
    "artist_image_link": show.artist.image_link,
    "start_time": str(show.start_time)
      })

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  new_show = Show()
  new_show.artist_id = form.artist_id.data
  new_show.venue_id = form.venue_id.data
  dateAndTime = form.start_time.data
  
  new_show.start_time = form.start_time.data
  try:
    db.session.add(new_show)
    # on successful db insert, flash success
    db.session.commit()
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('Show could not be listed. please make sure that your ids are correct')
  finally:
    db.session.close()
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
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
