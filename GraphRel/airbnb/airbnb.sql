CREATE DATABASE TesteRel; 
\c TesteRel
CREATE TYPE NEIGHBOURHOOD_NEIGHBOURHOOD_GROUP_ENUM AS ENUM("Queens", "Brooklyn", "Staten Island", "Bronx", "Manhattan")


/*Criando tabelas com atributos, tipos e PK*/
CREATE TABLE host (
  host_id VARCHAR(100) UNIQUE NOT NULL,
  host_name VARCHAR(100) NOT NULL,
  CONSTRAINT pk_host PRIMARY KEY (host_id) 
);

CREATE TABLE review (
  date VARCHAR(100) UNIQUE NOT NULL,
  CONSTRAINT pk_review PRIMARY KEY (date) 
);

CREATE TABLE listing (
  minimum_nights INTEGER NOT NULL,
  neighbourhood_group VARCHAR(100),
  availability_365 INTEGER NOT NULL,
  room_type VARCHAR(100) NOT NULL,
  number_of_reviews_ltm INTEGER NOT NULL,
  id VARCHAR(100) UNIQUE NOT NULL,
  number_of_reviews INTEGER NOT NULL,
  price INTEGER,
  last_review VARCHAR(100),
  reviews_per_month REAL,
  name VARCHAR(100) NOT NULL,
  longitude REAL NOT NULL,
  latitude REAL NOT NULL,
  calculated_host_listings_count INTEGER NOT NULL,
  neighbourhood VARCHAR(100) NOT NULL,
  license VARCHAR(100),
  CONSTRAINT pk_listing PRIMARY KEY (id) 
);

CREATE TABLE neighbourhood (
  neighbourhood_group NEIGHBOURHOOD_NEIGHBOURHOOD_GROUP_ENUM,
  neighbourhood VARCHAR(100) UNIQUE NOT NULL,
  CONSTRAINT pk_neighbourhood PRIMARY KEY (neighbourhood) 
);

/*Finalizada a criacao de tabelas (e especializacoes)*/

/*Inicio de tratamento de relacionamentos:*/
/*Criacao de rel (1:N)*/
ALTER TABLE listing ADD COLUMN host_host_id VARCHAR(20),
FOREIGN KEY (host_host_id) REFERENCES host(host_id);

/*Finalizado criacao de rel (1:N)*/

/*Criacao de rel (N:N)*/
CREATE TABLE REVIEW_reviews_LISTING (
  review_date VARCHAR(20),
  listing_id ['STR'],
,
  FOREIGN KEY (review_date) REFERENCES review(date),
  FOREIGN KEY (listing_id) REFERENCES listing(id)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:1)*/
ALTER TABLE listing ADD COLUMN neighbourhood_neighbourhood VARCHAR(20),
FOREIGN KEY (neighbourhood_neighbourhood) REFERENCES neighbourhood(neighbourhood);

/*Criacao de rel (N:1) finalizado*/

