from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(600))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(200))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(600))

    shows = db.relationship('show', back_populates='venue')

    artists = db.relationship('artist', secondary='show', backref=db.backref('list_artist', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(600))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(200))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(600))

    shows = db.relationship('show', back_populates='artist')

    venues = db.relationship('venue', secondary='show', backref=db.backref('list_venue', lazy=True))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class show(db.Model):
   __tablename__ = 'show'

   id = db.Column(db.Integer, primary_key=True, autoincrement=True)
   artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
   venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'))
   start_time = db.Column(db.DateTime)

  # Relationships to Artist and Venue
   artist = db.relationship('artist', back_populates="shows")
   venue = db.relationship('venue', back_populates="shows")
