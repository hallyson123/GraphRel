

/*Criando tabelas com atributos, tipos e PK*/
CREATE TABLE movie (
  budget BIGINT,
  movieId VARCHAR UNIQUE,
  tmdbId VARCHAR UNIQUE,
  imdbVotes BIGINT,
  runtime BIGINT,
  imdbId VARCHAR,
  url VARCHAR,
  plot VARCHAR,
  released VARCHAR,
  imdbRating REAL,
  title VARCHAR,
  poster VARCHAR,
  year BIGINT,
  revenue BIGINT,
  CONSTRAINT pk_movie PRIMARY KEY (movieId, tmdbId) 
);

CREATE TABLE genre (
  name VARCHAR UNIQUE,
  CONSTRAINT pk_genre PRIMARY KEY (name) 
);

CREATE TABLE user_table (
  name VARCHAR,
  userId VARCHAR UNIQUE,
  CONSTRAINT pk_user PRIMARY KEY (userId) 
);

CREATE TABLE person (
  id SERIAL PRIMARY KEY,
  name VARCHAR
);

CREATE TABLE person_actor (
  id SERIAL PRIMARY KEY,
  born DATE,
  bornIn VARCHAR,
  tmdbId VARCHAR,
  died DATE,
  name VARCHAR,
  imdbId VARCHAR,
  url VARCHAR,
  bio VARCHAR,
  poster VARCHAR
);

CREATE TABLE person_actor_director (
  id SERIAL PRIMARY KEY,
  born DATE,
  bornIn VARCHAR,
  tmdbId VARCHAR,
  bio VARCHAR,
  died DATE,
  name VARCHAR,
  poster VARCHAR,
  imdbId VARCHAR,
  url VARCHAR
);

CREATE TABLE person_director (
  id SERIAL PRIMARY KEY,
  born DATE,
  bornIn VARCHAR,
  tmdbId VARCHAR,
  bio VARCHAR,
  died DATE,
  name VARCHAR,
  imdbId VARCHAR,
  url VARCHAR,
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

