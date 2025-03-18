

/*Criando tabelas com atributos, tipos e PK*/
CREATE TABLE movie (
  budget BIGINT,
  movieId VARCHAR UNIQUE NOT NULL,
  tmdbId VARCHAR UNIQUE NOT NULL,
  imdbVotes BIGINT NOT NULL,
  runtime BIGINT NOT NULL,
  imdbId VARCHAR NOT NULL,
  url VARCHAR NOT NULL,
  plot VARCHAR NOT NULL,
  released VARCHAR NOT NULL,
  imdbRating REAL NOT NULL,
  title VARCHAR NOT NULL,
  poster VARCHAR NOT NULL,
  year BIGINT NOT NULL,
  revenue BIGINT,
  CONSTRAINT pk_movie PRIMARY KEY (movieId, tmdbId) 
);

CREATE TABLE genre (
  name VARCHAR UNIQUE NOT NULL,
  CONSTRAINT pk_genre PRIMARY KEY (name) 
);

CREATE TABLE user_table (
  name VARCHAR NOT NULL,
  userId VARCHAR UNIQUE NOT NULL,
  CONSTRAINT pk_user PRIMARY KEY (userId) 
);

CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  name VARCHAR NOT NULL
);

CREATE TABLE movie_countries_list (
  movie_movieId_id VARCHAR NOT NULL,
  movie_tmdbId_id VARCHAR NOT NULL,
  countries VARCHAR NOT NULL,
  FOREIGN KEY (movie_movieId_id) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId_id) REFERENCES movie(tmdbId)
);

CREATE TABLE movie_languages_list (
  movie_movieId_id VARCHAR NOT NULL,
  movie_tmdbId_id VARCHAR NOT NULL,
  languages VARCHAR NOT NULL,
  FOREIGN KEY (movie_movieId_id) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId_id) REFERENCES movie(tmdbId)
);

CREATE TABLE person_actor (
  id SERIAL PRIMARY KEY,
  born DATE,
  bornIn VARCHAR,
  tmdbId VARCHAR NOT NULL,
  died DATE,
  name VARCHAR NOT NULL,
  imdbId VARCHAR NOT NULL,
  url VARCHAR NOT NULL,
  bio VARCHAR,
  poster VARCHAR
);

CREATE TABLE person_actor_director (
  id SERIAL PRIMARY KEY,
  born DATE NOT NULL,
  bornIn VARCHAR NOT NULL,
  tmdbId VARCHAR NOT NULL,
  bio VARCHAR,
  died DATE,
  name VARCHAR NOT NULL,
  poster VARCHAR,
  imdbId VARCHAR NOT NULL,
  url VARCHAR NOT NULL
);

CREATE TABLE person_director (
  id SERIAL PRIMARY KEY,
  born DATE,
  bornIn VARCHAR,
  tmdbId VARCHAR NOT NULL,
  bio VARCHAR,
  died DATE,
  name VARCHAR NOT NULL,
  imdbId VARCHAR NOT NULL,
  url VARCHAR NOT NULL,
  poster VARCHAR
);

/*Finalizada a criacao de tabelas (e especializacoes)*/

/*######################################################*/

/*Inicio de tratamento de relacionamentos:*/
/*Criacao de rel (N:N)*/
CREATE TABLE MOVIE_in_genre_GENRE (
  movie_movieId VARCHAR,
  movie_tmdbId VARCHAR,
  genre_name VARCHAR,
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId),
  FOREIGN KEY (genre_name) REFERENCES genre(name)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE USER_TABLE_rated_MOVIE (
  user_table_userId VARCHAR,
  movie_movieId VARCHAR,
  movie_tmdbId VARCHAR,
  timestamp INTEGER,
  rating REAL,
  FOREIGN KEY (user_table_userId) REFERENCES user_table(userId),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_ACTOR_acted_in_MOVIE (
  person_actor_id INTEGER,
  movie_movieId VARCHAR,
  movie_tmdbId VARCHAR,
  role VARCHAR,
  FOREIGN KEY (person_actor_id) REFERENCES person_actor(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_ACTOR_DIRECTOR_acted_in_MOVIE (
  person_actor_director_id INTEGER,
  movie_movieId VARCHAR,
  movie_tmdbId VARCHAR,
  role VARCHAR,
  FOREIGN KEY (person_actor_director_id) REFERENCES person_actor_director(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_ACTOR_DIRECTOR_directed_MOVIE (
  person_actor_director_id INTEGER,
  movie_movieId VARCHAR,
  movie_tmdbId VARCHAR,
  role VARCHAR,
  FOREIGN KEY (person_actor_director_id) REFERENCES person_actor_director(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_DIRECTOR_directed_MOVIE (
  person_director_id INTEGER,
  movie_movieId VARCHAR,
  movie_tmdbId VARCHAR,
  role VARCHAR,
  FOREIGN KEY (person_director_id) REFERENCES person_director(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

