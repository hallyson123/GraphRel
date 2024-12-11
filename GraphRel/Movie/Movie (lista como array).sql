CREATE DATABASE TesteRel; 
\c TesteRel

CREATE TYPE USER_TABLE_RATEDREL_MOVIE_RATING_ENUM AS ENUM('0.5', '1.0', '2.0', '3.0', '2.5', '4.0', '3.5', '5.0', '4.5', '1.5');

/*Criando tabelas com atributos, tipos e PK*/
CREATE TABLE movie (
  budget INTEGER,
  movieId VARCHAR(100) UNIQUE NOT NULL,
  tmdbId VARCHAR(100) UNIQUE NOT NULL,
  imdbVotes INTEGER NOT NULL,
  countries VARCHAR(100)[] NOT NULL,
  runtime INTEGER NOT NULL,
  imdbId VARCHAR(100) NOT NULL,
  url VARCHAR(100) NOT NULL,
  plot VARCHAR(100) NOT NULL,
  released VARCHAR(100) NOT NULL,
  languages VARCHAR(100)[] NOT NULL,
  imdbRating REAL NOT NULL,
  title VARCHAR(100) NOT NULL,
  poster VARCHAR(100) NOT NULL,
  year INTEGER NOT NULL,
  revenue INTEGER,
  CONSTRAINT pk_movie PRIMARY KEY (movieId, tmdbId)
);

CREATE TABLE genre (
  name VARCHAR(100) UNIQUE NOT NULL,
  CONSTRAINT pk_genre PRIMARY KEY (name) 
);

CREATE TABLE user_table (
  name VARCHAR(100) NOT NULL,
  userId VARCHAR(100) UNIQUE NOT NULL,
  CONSTRAINT pk_user PRIMARY KEY (userId) 
);

CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);

CREATE TYPE PERSON_ACTOR_TIPO_ENUM AS ENUM('Person', 'Actor')

CREATE TABLE person_actor (
  id SERIAL PRIMARY KEY,
  tipo PERSON_ACTOR_TIPO_ENUM,
  born DATE,
  bornIn VARCHAR(100),
  tmdbId VARCHAR(100) NOT NULL,
  died DATE,
  name VARCHAR(100) NOT NULL,
  imdbId VARCHAR(100) NOT NULL,
  url VARCHAR(100) NOT NULL,
  bio VARCHAR(100),
  poster VARCHAR(100)
);

CREATE TYPE PERSON_ACTOR_DIRECTOR_TIPO_ENUM AS ENUM('Person', 'Actor', 'Director')

CREATE TABLE person_actor_director (
  id SERIAL PRIMARY KEY,
  tipo PERSON_ACTOR_DIRECTOR_TIPO_ENUM,
  born DATE NOT NULL,
  bornIn VARCHAR(100) NOT NULL,
  tmdbId VARCHAR(100) NOT NULL,
  bio VARCHAR(100),
  died DATE,
  name VARCHAR(100) NOT NULL,
  poster VARCHAR(100),
  imdbId VARCHAR(100) NOT NULL,
  url VARCHAR(100) NOT NULL
);

CREATE TYPE PERSON_DIRECTOR_TIPO_ENUM AS ENUM('Person', 'Director')

CREATE TABLE person_director (
  id SERIAL PRIMARY KEY,
  tipo PERSON_DIRECTOR_TIPO_ENUM,
  born DATE,
  bornIn VARCHAR(100),
  tmdbId VARCHAR(100) NOT NULL,
  bio VARCHAR(100),
  died DATE,
  name VARCHAR(100) NOT NULL,
  imdbId VARCHAR(100) NOT NULL,
  url VARCHAR(100) NOT NULL,
  poster VARCHAR(100)
);

/*Finalizada a criacao de tabelas (e especializacoes)*/

/*Inicio de tratamento de relacionamentos:*/
/*Criacao de rel (N:N)*/
CREATE TABLE MOVIE_in_genre_GENRE (
  movie_movieId VARCHAR(20),
  movie_tmdbId VARCHAR(20),
  genre_name VARCHAR(20),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId),
  FOREIGN KEY (genre_name) REFERENCES genre(name)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE USER_TABLE_rated_MOVIE (
  user_table_userId VARCHAR(100),
  movie_movieId VARCHAR(100),
  movie_tmdbId VARCHAR(100),
  timestamp INTEGER NOT NULL,
  rating USER_TABLE_RATEDREL_MOVIE_RATING_ENUM NOT NULL,
  FOREIGN KEY (user_table_userId) REFERENCES user_table(userId),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_ACTOR_acted_in_MOVIE (
  person_actor_id INTEGER,
  movie_movieId VARCHAR(100),
  movie_tmdbId VARCHAR(100),
  role VARCHAR(100) NOT NULL,
  FOREIGN KEY (person_actor_id) REFERENCES person_actor(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_ACTOR_DIRECTOR_acted_in_MOVIE (
  person_actor_director_id INTEGER,
  movie_movieId VARCHAR(100),
  movie_tmdbId VARCHAR(100),
  role VARCHAR(100) NOT NULL,
  FOREIGN KEY (person_actor_director_id) REFERENCES person_actor_director(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_ACTOR_DIRECTOR_directed_MOVIE (
  person_actor_director_id INTEGER,
  movie_movieId VARCHAR(100),
  movie_tmdbId VARCHAR(100),
  role VARCHAR(100),
  FOREIGN KEY (person_actor_director_id) REFERENCES person_actor_director(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:N)*/
CREATE TABLE PERSON_DIRECTOR_directed_MOVIE (
  person_director_id INTEGER,
  movie_movieId VARCHAR(100),
  movie_tmdbId VARCHAR(100),
  role VARCHAR(100),
  FOREIGN KEY (person_director_id) REFERENCES person_director(id),
  FOREIGN KEY (movie_movieId) REFERENCES movie(movieId),
  FOREIGN KEY (movie_tmdbId) REFERENCES movie(tmdbId)
);
/*Criacao de rel (N:N) finalizada*/