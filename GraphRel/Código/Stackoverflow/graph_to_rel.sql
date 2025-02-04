

/*Criando tabelas com atributos, tipos e PK*/
CREATE TABLE question (
  creation_date BIGINT NOT NULL,
  title VARCHAR NOT NULL,
  link VARCHAR NOT NULL,
  body_markdown VARCHAR NOT NULL,
  answer_count BIGINT NOT NULL,
  uuid BIGINT UNIQUE NOT NULL,
  view_count BIGINT NOT NULL,
  accepted_answer_id BIGINT,
  CONSTRAINT pk_question PRIMARY KEY (uuid) 
);

CREATE TABLE user_table (
  display_name VARCHAR NOT NULL,
  uuid BIGINT UNIQUE NOT NULL,
  CONSTRAINT pk_user PRIMARY KEY (uuid) 
);

CREATE TABLE tag (
  name VARCHAR UNIQUE NOT NULL,
  link VARCHAR NOT NULL,
  CONSTRAINT pk_tag PRIMARY KEY (name) 
);

CREATE TABLE answer (
  is_accepted BOOL NOT NULL,
  title VARCHAR NOT NULL,
  link VARCHAR NOT NULL,
  score BIGINT NOT NULL,
  body_markdown VARCHAR NOT NULL,
  uuid BIGINT UNIQUE NOT NULL,
  CONSTRAINT pk_answer PRIMARY KEY (uuid) 
);

CREATE TABLE comment (
  link VARCHAR NOT NULL,
  score BIGINT NOT NULL,
  uuid BIGINT UNIQUE NOT NULL,
  CONSTRAINT pk_comment PRIMARY KEY (uuid) 
);

/*Finalizada a criacao de tabelas (e especializacoes)*/

/*######################################################*/

/*Inicio de tratamento de relacionamentos:*/
/*Criacao de rel (N:N)*/
CREATE TABLE QUESTION_tagged_TAG (
  question_uuid INTEGER,
  tag_name VARCHAR,
  FOREIGN KEY (question_uuid) REFERENCES question(uuid),
  FOREIGN KEY (tag_name) REFERENCES tag(name)
);
/*Criacao de rel (N:N) finalizada*/

/*Criacao de rel (1:N)*/
ALTER TABLE answer ADD COLUMN user_table_uuid INTEGER;
ALTER TABLE answer ADD FOREIGN KEY (user_table_uuid) REFERENCES user_table(uuid);

/*Finalizado criacao de rel (1:N)*/

/*Criacao de rel (1:N)*/
ALTER TABLE question ADD COLUMN user_table_uuid INTEGER;
ALTER TABLE question ADD FOREIGN KEY (user_table_uuid) REFERENCES user_table(uuid);

/*Finalizado criacao de rel (1:N)*/

/*Criacao de rel (1:N)*/
ALTER TABLE comment ADD COLUMN user_table_uuid INTEGER;
ALTER TABLE comment ADD FOREIGN KEY (user_table_uuid) REFERENCES user_table(uuid);

/*Finalizado criacao de rel (1:N)*/

/*Criacao de rel (N:1)*/
ALTER TABLE answer ADD COLUMN question_uuid INTEGER;
ALTER TABLE answer ADD FOREIGN KEY (question_uuid) REFERENCES question(uuid);

/*Criacao de rel (N:1) finalizado*/

/*Criacao de rel (N:1)*/
ALTER TABLE comment ADD COLUMN question_uuid INTEGER;
ALTER TABLE comment ADD FOREIGN KEY (question_uuid) REFERENCES question(uuid);

/*Criacao de rel (N:1) finalizado*/

