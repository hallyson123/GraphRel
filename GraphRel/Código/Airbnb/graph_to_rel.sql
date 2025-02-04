

/*Criando tabelas com atributos, tipos e PK*/
CREATE TABLE host (
  host_id VARCHAR UNIQUE NOT NULL,
  host_name VARCHAR NOT NULL,
  CONSTRAINT pk_host PRIMARY KEY (host_id) 
);

CREATE TABLE review (
  date VARCHAR UNIQUE NOT NULL,
  CONSTRAINT pk_review PRIMARY KEY (date) 
);

CREATE TABLE listing (
  minimum_nights BIGINT NOT NULL,
  neighbourhood_group VARCHAR,
  availability_365 BIGINT NOT NULL,
  room_type VARCHAR NOT NULL,
  number_of_reviews_ltm BIGINT NOT NULL,
  id VARCHAR UNIQUE NOT NULL,
  number_of_reviews BIGINT NOT NULL,
  price BIGINT,
  last_review VARCHAR,
  reviews_per_month REAL,
  name VARCHAR NOT NULL,
  longitude REAL NOT NULL,
  latitude REAL NOT NULL,
  calculated_host_listings_count BIGINT NOT NULL,
  neighbourhood VARCHAR NOT NULL,
  license VARCHAR,
  CONSTRAINT pk_listing PRIMARY KEY (id) 
);

CREATE TABLE neighbourhood (
  neighbourhood_group NEIGHBOURHOOD_NEIGHBOURHOOD_GROUP_ENUM,
  neighbourhood VARCHAR UNIQUE NOT NULL,
  CONSTRAINT pk_neighbourhood PRIMARY KEY (neighbourhood) 
);

/*Finalizada a criacao de tabelas (e especializacoes)*/

/*######################################################*/

/*Inicio de tratamento de relacionamentos:*/
/*Criacao de rel (1:N)*/
ALTER TABLE listing ADD COLUMN host_host_id VARCHAR;
ALTER TABLE listing ADD FOREIGN KEY (host_host_id) REFERENCES host(host_id);

/*Finalizado criacao de rel (1:N)*/

/*Criacao de rel (N:N)*/
CREATE TABLE REVIEW_reviews_LISTING (
  review_date VARCHAR,
  listing_id VARCHAR,
  FOREIGN KEY (review_date) REFERENCES review(date),
  FOREIGN KEY (listing_id) REFERENCES listing(id)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (N:1)*/
ALTER TABLE listing ADD COLUMN neighbourhood_neighbourhood VARCHAR;
ALTER TABLE listing ADD FOREIGN KEY (neighbourhood_neighbourhood) REFERENCES neighbourhood(neighbourhood);

/*Criacao de rel (N:1) finalizado*/

