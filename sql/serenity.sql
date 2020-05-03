-- Database generated with pgModeler (PostgreSQL Database Modeler).
-- pgModeler  version: 0.9.2_snapshot20191127
-- PostgreSQL version: 11.0
-- Project Site: pgmodeler.io
-- Model Author: ---


-- Database creation must be done outside a multicommand file.
-- These commands were put in this file only as a convenience.
-- -- object: serenity | type: DATABASE --
-- -- DROP DATABASE IF EXISTS serenity;
-- CREATE DATABASE serenity;
-- -- ddl-end --
-- 

-- object: serenity | type: SCHEMA --
-- DROP SCHEMA IF EXISTS serenity CASCADE;
CREATE SCHEMA serenity;
-- ddl-end --
-- ALTER SCHEMA serenity OWNER TO postgres;
-- ddl-end --

SET search_path TO pg_catalog,public,serenity;
-- ddl-end --

-- object: serenity.exchange_trade | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_trade CASCADE;
CREATE TABLE serenity.exchange_trade (
	exchange_trade_id bigint NOT NULL,
	exchange_id integer NOT NULL,
	instrument_id integer NOT NULL,
	side_id smallint NOT NULL,
	trade_id bigint NOT NULL,
	trade_price decimal(24,16) NOT NULL,
	quantity decimal(24,16) NOT NULL,
	is_auction_fill bool NOT NULL,
	trade_time timestamp NOT NULL,
	CONSTRAINT exchange_trade_pk PRIMARY KEY (exchange_trade_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_trade OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_order_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_order_seq CASCADE;
CREATE SEQUENCE serenity.exchange_order_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_order_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_fill_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_fill_seq CASCADE;
CREATE SEQUENCE serenity.exchange_fill_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_fill_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange CASCADE;
CREATE TABLE serenity.exchange (
	exchange_id integer NOT NULL,
	exchange_code varchar(32) NOT NULL,
	CONSTRAINT exchange_pk PRIMARY KEY (exchange_id),
	CONSTRAINT exchange_code_uq UNIQUE (exchange_code)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.exchange (exchange_id, exchange_code) VALUES (E'1', E'CoinbasePro');
-- ddl-end --
INSERT INTO serenity.exchange (exchange_id, exchange_code) VALUES (E'2', E'Gemini');
-- ddl-end --
INSERT INTO serenity.exchange (exchange_id, exchange_code) VALUES (E'3', E'Binance');
-- ddl-end --
INSERT INTO serenity.exchange (exchange_id, exchange_code) VALUES (E'4', E'Coinbase');
-- ddl-end --
INSERT INTO serenity.exchange (exchange_id, exchange_code) VALUES (E'5', E'Phemex');
-- ddl-end --

-- object: serenity.exchange_order | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_order CASCADE;
CREATE TABLE serenity.exchange_order (
	exchange_order_id integer NOT NULL DEFAULT nextval('serenity.exchange_order_seq'::regclass),
	exchange_id integer NOT NULL,
	exchange_instrument_id integer NOT NULL,
	order_type_id integer NOT NULL,
	exchange_account_id integer NOT NULL,
	side_id smallint NOT NULL,
	time_in_force_id integer NOT NULL,
	exchange_order_uuid varchar(64) NOT NULL,
	price decimal(24,16),
	quantity decimal(24,16) NOT NULL,
	create_time timestamp NOT NULL,
	CONSTRAINT exchange_order_pk PRIMARY KEY (exchange_order_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_order OWNER TO postgres;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_trade DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_trade ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.destination_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.destination_seq CASCADE;
CREATE SEQUENCE serenity.destination_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.destination_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_account_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_account_seq CASCADE;
CREATE SEQUENCE serenity.exchange_account_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_account_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_account | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_account CASCADE;
CREATE TABLE serenity.exchange_account (
	exchange_account_id integer NOT NULL DEFAULT nextval('serenity.exchange_account_seq'::regclass),
	exchange_id integer NOT NULL,
	exchange_account_num varchar(256) NOT NULL,
	CONSTRAINT exchange_account_pk PRIMARY KEY (exchange_account_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_account OWNER TO postgres;
-- ddl-end --

-- object: serenity.order_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.order_seq CASCADE;
CREATE SEQUENCE serenity.order_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.order_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.fill_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.fill_seq CASCADE;
CREATE SEQUENCE serenity.fill_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.fill_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity."order" | type: TABLE --
-- DROP TABLE IF EXISTS serenity."order" CASCADE;
CREATE TABLE serenity."order" (
	order_id integer NOT NULL DEFAULT nextval('serenity.order_seq'::regclass),
	order_type_id integer NOT NULL,
	instrument_id integer NOT NULL,
	side_id smallint NOT NULL,
	trading_account_id integer NOT NULL,
	time_in_force_id integer NOT NULL,
	destination_id integer NOT NULL,
	parent_order_id integer,
	price decimal(24,16),
	quantity decimal(24,16) NOT NULL,
	create_time timestamp NOT NULL,
	CONSTRAINT order_pk PRIMARY KEY (order_id)

);
-- ddl-end --
-- ALTER TABLE serenity."order" OWNER TO postgres;
-- ddl-end --

-- object: exchange_account_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS exchange_account_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT exchange_account_fk FOREIGN KEY (exchange_account_id)
REFERENCES serenity.exchange_account (exchange_account_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_fill | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_fill CASCADE;
CREATE TABLE serenity.exchange_fill (
	exchange_fill_id integer NOT NULL DEFAULT nextval('serenity.exchange_fill_seq'::regclass),
	exchange_order_id integer NOT NULL,
	fill_price decimal(24,16) NOT NULL,
	quantity decimal(24,16) NOT NULL,
	fees decimal(24,16) NOT NULL,
	trade_id bigint NOT NULL,
	create_time timestamp NOT NULL,
	CONSTRAINT exchange_fill_pk PRIMARY KEY (exchange_fill_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_fill OWNER TO postgres;
-- ddl-end --

-- object: serenity.instrument_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.instrument_seq CASCADE;
CREATE SEQUENCE serenity.instrument_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.instrument_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_instrument_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_instrument_seq CASCADE;
CREATE SEQUENCE serenity.exchange_instrument_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_instrument_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.instrument | type: TABLE --
-- DROP TABLE IF EXISTS serenity.instrument CASCADE;
CREATE TABLE serenity.instrument (
	instrument_id integer NOT NULL DEFAULT nextval('serenity.instrument_seq'::regclass),
	instrument_type_id integer,
	instrument_code varchar(32) NOT NULL,
	CONSTRAINT instrument_pk PRIMARY KEY (instrument_id)

);
-- ddl-end --
-- ALTER TABLE serenity.instrument OWNER TO postgres;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_instrument | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_instrument CASCADE;
CREATE TABLE serenity.exchange_instrument (
	exchange_instrument_id integer NOT NULL DEFAULT nextval('serenity.exchange_instrument_seq'::regclass),
	exchange_id integer NOT NULL,
	instrument_id integer NOT NULL,
	exchange_instrument_code varchar(32) NOT NULL,
	CONSTRAINT exchange_instrument_pk PRIMARY KEY (exchange_instrument_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_instrument OWNER TO postgres;
-- ddl-end --

-- object: serenity.currency_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.currency_seq CASCADE;
CREATE SEQUENCE serenity.currency_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.currency_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.currency_pair_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.currency_pair_seq CASCADE;
CREATE SEQUENCE serenity.currency_pair_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.currency_pair_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.currency_pair | type: TABLE --
-- DROP TABLE IF EXISTS serenity.currency_pair CASCADE;
CREATE TABLE serenity.currency_pair (
	currency_pair_id integer NOT NULL DEFAULT nextval('serenity.currency_pair_seq'::regclass),
	base_currency_id integer NOT NULL,
	quote_currency_id integer NOT NULL,
	instrument_id integer NOT NULL,
	CONSTRAINT currency_pair_pk PRIMARY KEY (currency_pair_id)

);
-- ddl-end --
-- ALTER TABLE serenity.currency_pair OWNER TO postgres;
-- ddl-end --

-- object: serenity.trading_account_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.trading_account_seq CASCADE;
CREATE SEQUENCE serenity.trading_account_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.trading_account_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.trading_account | type: TABLE --
-- DROP TABLE IF EXISTS serenity.trading_account CASCADE;
CREATE TABLE serenity.trading_account (
	trading_account_id integer NOT NULL DEFAULT nextval('serenity.trading_account_seq'::regclass),
	portfolio_id integer NOT NULL,
	trading_account_name varchar(256) NOT NULL,
	CONSTRAINT trading_account_pk PRIMARY KEY (trading_account_id)

);
-- ddl-end --
-- ALTER TABLE serenity.trading_account OWNER TO postgres;
-- ddl-end --

-- object: serenity.time_in_force | type: TABLE --
-- DROP TABLE IF EXISTS serenity.time_in_force CASCADE;
CREATE TABLE serenity.time_in_force (
	time_in_force_id integer NOT NULL,
	time_in_force_code varchar(32) NOT NULL,
	CONSTRAINT time_in_force_pk PRIMARY KEY (time_in_force_id)

);
-- ddl-end --
-- ALTER TABLE serenity.time_in_force OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.time_in_force (time_in_force_id, time_in_force_code) VALUES (E'1', E'Day');
-- ddl-end --
INSERT INTO serenity.time_in_force (time_in_force_id, time_in_force_code) VALUES (E'2', E'GTC');
-- ddl-end --
INSERT INTO serenity.time_in_force (time_in_force_id, time_in_force_code) VALUES (E'3', E'GTT');
-- ddl-end --
INSERT INTO serenity.time_in_force (time_in_force_id, time_in_force_code) VALUES (E'4', E'GTD');
-- ddl-end --
INSERT INTO serenity.time_in_force (time_in_force_id, time_in_force_code) VALUES (E'5', E'IOC');
-- ddl-end --
INSERT INTO serenity.time_in_force (time_in_force_id, time_in_force_code) VALUES (E'6', E'FOK');
-- ddl-end --

-- object: time_in_force_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS time_in_force_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT time_in_force_fk FOREIGN KEY (time_in_force_id)
REFERENCES serenity.time_in_force (time_in_force_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.order_type | type: TABLE --
-- DROP TABLE IF EXISTS serenity.order_type CASCADE;
CREATE TABLE serenity.order_type (
	order_type_id integer NOT NULL,
	order_type_code varchar(32) NOT NULL,
	CONSTRAINT order_type_pk PRIMARY KEY (order_type_id)

);
-- ddl-end --
-- ALTER TABLE serenity.order_type OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.order_type (order_type_id, order_type_code) VALUES (E'1', E'Market');
-- ddl-end --
INSERT INTO serenity.order_type (order_type_id, order_type_code) VALUES (E'2', E'Limit');
-- ddl-end --

-- object: order_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS order_type_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT order_type_fk FOREIGN KEY (order_type_id)
REFERENCES serenity.order_type (order_type_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_seq CASCADE;
CREATE SEQUENCE serenity.exchange_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.side | type: TABLE --
-- DROP TABLE IF EXISTS serenity.side CASCADE;
CREATE TABLE serenity.side (
	side_id smallint NOT NULL,
	side_code varchar(32) NOT NULL,
	CONSTRAINT side_pk PRIMARY KEY (side_id)

);
-- ddl-end --
-- ALTER TABLE serenity.side OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.side (side_id, side_code) VALUES (E'1', E'Buy');
-- ddl-end --
INSERT INTO serenity.side (side_id, side_code) VALUES (E'2', E'Sell');
-- ddl-end --

-- object: side_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_trade DROP CONSTRAINT IF EXISTS side_fk CASCADE;
ALTER TABLE serenity.exchange_trade ADD CONSTRAINT side_fk FOREIGN KEY (side_id)
REFERENCES serenity.side (side_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: side_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS side_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT side_fk FOREIGN KEY (side_id)
REFERENCES serenity.side (side_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: side_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS side_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT side_fk FOREIGN KEY (side_id)
REFERENCES serenity.side (side_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: order_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS order_type_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT order_type_fk FOREIGN KEY (order_type_id)
REFERENCES serenity.order_type (order_type_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: time_in_force_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS time_in_force_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT time_in_force_fk FOREIGN KEY (time_in_force_id)
REFERENCES serenity.time_in_force (time_in_force_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.portfolio_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.portfolio_seq CASCADE;
CREATE SEQUENCE serenity.portfolio_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.portfolio_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.portfolio | type: TABLE --
-- DROP TABLE IF EXISTS serenity.portfolio CASCADE;
CREATE TABLE serenity.portfolio (
	portfolio_id integer NOT NULL DEFAULT nextval('serenity.portfolio_seq'::regclass),
	portfolio_name varchar(256) NOT NULL,
	CONSTRAINT portfolio_pk PRIMARY KEY (portfolio_id)

);
-- ddl-end --
-- ALTER TABLE serenity.portfolio OWNER TO postgres;
-- ddl-end --

-- object: serenity.instrument_type | type: TABLE --
-- DROP TABLE IF EXISTS serenity.instrument_type CASCADE;
CREATE TABLE serenity.instrument_type (
	instrument_type_id integer NOT NULL,
	instrument_type_code varchar(32) NOT NULL,
	CONSTRAINT instrument_type_pk PRIMARY KEY (instrument_type_id)

);
-- ddl-end --
-- ALTER TABLE serenity.instrument_type OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.instrument_type (instrument_type_id, instrument_type_code) VALUES (E'1', E'CurrencyPair');
-- ddl-end --
INSERT INTO serenity.instrument_type (instrument_type_id, instrument_type_code) VALUES (E'2', E'Cash');
-- ddl-end --

-- object: instrument_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.instrument DROP CONSTRAINT IF EXISTS instrument_type_fk CASCADE;
ALTER TABLE serenity.instrument ADD CONSTRAINT instrument_type_fk FOREIGN KEY (instrument_type_id)
REFERENCES serenity.instrument_type (instrument_type_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.destination_type | type: TABLE --
-- DROP TABLE IF EXISTS serenity.destination_type CASCADE;
CREATE TABLE serenity.destination_type (
	destination_type_id integer NOT NULL,
	destination_type_code varchar(32) NOT NULL,
	CONSTRAINT destrination_type_pk PRIMARY KEY (destination_type_id)

);
-- ddl-end --
-- ALTER TABLE serenity.destination_type OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.destination_type (destination_type_id, destination_type_code) VALUES (E'1', E'Exchange');
-- ddl-end --
INSERT INTO serenity.destination_type (destination_type_id, destination_type_code) VALUES (E'2', E'Internal');
-- ddl-end --
INSERT INTO serenity.destination_type (destination_type_id, destination_type_code) VALUES (E'3', E'Algo');
-- ddl-end --

-- object: serenity.exchange_destination_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_destination_seq CASCADE;
CREATE SEQUENCE serenity.exchange_destination_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_destination_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_destination | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_destination CASCADE;
CREATE TABLE serenity.exchange_destination (
	exchange_destination_id integer NOT NULL,
	exchange_id integer NOT NULL,
	destination_id integer NOT NULL,
	CONSTRAINT exchange_destination_pk PRIMARY KEY (exchange_destination_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_destination OWNER TO postgres;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: currency_pair_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS currency_pair_uq CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT currency_pair_uq UNIQUE (instrument_id);
-- ddl-end --

-- object: serenity.fill | type: TABLE --
-- DROP TABLE IF EXISTS serenity.fill CASCADE;
CREATE TABLE serenity.fill (
	fill_id integer NOT NULL DEFAULT nextval('serenity.fill_seq'::regclass),
	order_id integer,
	trade_id bigint NOT NULL,
	fill_price decimal(24,16) NOT NULL,
	quantity decimal(24,16) NOT NULL,
	create_time timestamp NOT NULL,
	CONSTRAINT fill_pk PRIMARY KEY (fill_id)

);
-- ddl-end --
-- ALTER TABLE serenity.fill OWNER TO postgres;
-- ddl-end --

-- object: serenity.destination | type: TABLE --
-- DROP TABLE IF EXISTS serenity.destination CASCADE;
CREATE TABLE serenity.destination (
	destination_id integer NOT NULL DEFAULT nextval('serenity.destination_seq'::regclass),
	destination_type_id integer,
	CONSTRAINT destination_pk PRIMARY KEY (destination_id)

);
-- ddl-end --
-- ALTER TABLE serenity.destination OWNER TO postgres;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_account DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_account ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: destination_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS destination_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT destination_fk FOREIGN KEY (destination_id)
REFERENCES serenity.destination (destination_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_destination DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_destination ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_exchange_destination_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_destination DROP CONSTRAINT IF EXISTS exchange_exchange_destination_uq CASCADE;
ALTER TABLE serenity.exchange_destination ADD CONSTRAINT exchange_exchange_destination_uq UNIQUE (exchange_id);
-- ddl-end --

-- object: destination_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.destination DROP CONSTRAINT IF EXISTS destination_type_fk CASCADE;
ALTER TABLE serenity.destination ADD CONSTRAINT destination_type_fk FOREIGN KEY (destination_type_id)
REFERENCES serenity.destination_type (destination_type_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: destination_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_destination DROP CONSTRAINT IF EXISTS destination_fk CASCADE;
ALTER TABLE serenity.exchange_destination ADD CONSTRAINT destination_fk FOREIGN KEY (destination_id)
REFERENCES serenity.destination (destination_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_destination_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_destination DROP CONSTRAINT IF EXISTS exchange_destination_uq CASCADE;
ALTER TABLE serenity.exchange_destination ADD CONSTRAINT exchange_destination_uq UNIQUE (destination_id);
-- ddl-end --

-- object: portfolio_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.trading_account DROP CONSTRAINT IF EXISTS portfolio_fk CASCADE;
ALTER TABLE serenity.trading_account ADD CONSTRAINT portfolio_fk FOREIGN KEY (portfolio_id)
REFERENCES serenity.portfolio (portfolio_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: trading_account_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS trading_account_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT trading_account_fk FOREIGN KEY (trading_account_id)
REFERENCES serenity.trading_account (trading_account_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_trade DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.exchange_trade ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: order_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.fill DROP CONSTRAINT IF EXISTS order_fk CASCADE;
ALTER TABLE serenity.fill ADD CONSTRAINT order_fk FOREIGN KEY (order_id)
REFERENCES serenity."order" (order_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS exchange_instrument_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT exchange_instrument_fk FOREIGN KEY (exchange_instrument_id)
REFERENCES serenity.exchange_instrument (exchange_instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_order DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_order ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_order_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_fill DROP CONSTRAINT IF EXISTS exchange_order_fk CASCADE;
ALTER TABLE serenity.exchange_fill ADD CONSTRAINT exchange_order_fk FOREIGN KEY (exchange_order_id)
REFERENCES serenity.exchange_order (exchange_order_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_trade_id_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_trade_id_idx CASCADE;
CREATE UNIQUE INDEX exchange_trade_id_idx ON serenity.exchange_trade
	USING btree
	(
	  trade_id
	);
-- ddl-end --

-- object: parent_order_id_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.parent_order_id_idx CASCADE;
CREATE INDEX parent_order_id_idx ON serenity."order"
	USING btree
	(
	  parent_order_id
	);
-- ddl-end --

-- object: trading_account_name_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.trading_account_name_idx CASCADE;
CREATE UNIQUE INDEX trading_account_name_idx ON serenity.trading_account
	USING btree
	(
	  trading_account_name
	);
-- ddl-end --

-- object: portfolio_name_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.portfolio_name_idx CASCADE;
CREATE UNIQUE INDEX portfolio_name_idx ON serenity.portfolio
	USING btree
	(
	  portfolio_name
	);
-- ddl-end --

-- object: exchange_order_uuid_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_order_uuid_idx CASCADE;
CREATE UNIQUE INDEX exchange_order_uuid_idx ON serenity.exchange_order
	USING btree
	(
	  exchange_order_uuid
	);
-- ddl-end --

-- object: trade_id_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.trade_id_idx CASCADE;
CREATE INDEX trade_id_idx ON serenity.exchange_fill
	USING btree
	(
	  trade_id
	);
-- ddl-end --

-- object: exchange_code | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_code CASCADE;
CREATE UNIQUE INDEX exchange_code ON serenity.exchange
	USING btree
	(
	  exchange_code
	);
-- ddl-end --

-- object: exchange_account_num_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_account_num_idx CASCADE;
CREATE UNIQUE INDEX exchange_account_num_idx ON serenity.exchange_account
	USING btree
	(
	  exchange_account_num,
	  exchange_id
	);
-- ddl-end --

-- object: order_tyoe_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.order_tyoe_code_idx CASCADE;
CREATE UNIQUE INDEX order_tyoe_code_idx ON serenity.order_type
	USING btree
	(
	  order_type_code
	);
-- ddl-end --

-- object: destination_type_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.destination_type_code_idx CASCADE;
CREATE UNIQUE INDEX destination_type_code_idx ON serenity.destination_type
	USING btree
	(
	  destination_type_code
	);
-- ddl-end --

-- object: side_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.side_code_idx CASCADE;
CREATE UNIQUE INDEX side_code_idx ON serenity.side
	USING btree
	(
	  side_code
	);
-- ddl-end --

-- object: instrument_type_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.instrument_type_code_idx CASCADE;
CREATE UNIQUE INDEX instrument_type_code_idx ON serenity.instrument_type
	USING btree
	(
	  instrument_type_code
	);
-- ddl-end --

-- object: tif_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.tif_code_idx CASCADE;
CREATE UNIQUE INDEX tif_code_idx ON serenity.time_in_force
	USING btree
	(
	  time_in_force_code
	);
-- ddl-end --

-- object: instrument_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.instrument_code_idx CASCADE;
CREATE UNIQUE INDEX instrument_code_idx ON serenity.instrument
	USING btree
	(
	  instrument_code
	);
-- ddl-end --

-- object: fill_trade_id_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.fill_trade_id_idx CASCADE;
CREATE UNIQUE INDEX fill_trade_id_idx ON serenity.fill
	USING btree
	(
	  trade_id
	);
-- ddl-end --

-- object: serenity.position_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.position_seq CASCADE;
CREATE SEQUENCE serenity.position_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.position_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.cash_instrument_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.cash_instrument_seq CASCADE;
CREATE SEQUENCE serenity.cash_instrument_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.cash_instrument_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity."position" | type: TABLE --
-- DROP TABLE IF EXISTS serenity."position" CASCADE;
CREATE TABLE serenity."position" (
	position_id integer NOT NULL DEFAULT nextval('serenity.position_seq'::regclass),
	instrument_id integer,
	trading_account_id integer,
	position_date date NOT NULL,
	quantity decimal(24,16) NOT NULL,
	update_time timestamp NOT NULL,
	CONSTRAINT position_pk PRIMARY KEY (position_id)

);
-- ddl-end --
-- ALTER TABLE serenity."position" OWNER TO postgres;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."position" DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity."position" ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.cash_instrument | type: TABLE --
-- DROP TABLE IF EXISTS serenity.cash_instrument CASCADE;
CREATE TABLE serenity.cash_instrument (
	cash_instrument_id integer NOT NULL DEFAULT nextval('serenity.cash_instrument_seq'::regclass),
	currency_id integer NOT NULL,
	instrument_id integer NOT NULL,
	CONSTRAINT cash_instrument_pk PRIMARY KEY (cash_instrument_id)

);
-- ddl-end --
-- ALTER TABLE serenity.cash_instrument OWNER TO postgres;
-- ddl-end --

-- object: serenity.currency | type: TABLE --
-- DROP TABLE IF EXISTS serenity.currency CASCADE;
CREATE TABLE serenity.currency (
	currency_id integer NOT NULL DEFAULT nextval('serenity.currency_seq'::regclass),
	currency_code varchar(8) NOT NULL,
	CONSTRAINT currency_pk PRIMARY KEY (currency_id)

);
-- ddl-end --
-- ALTER TABLE serenity.currency OWNER TO postgres;
-- ddl-end --

-- object: trading_account_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."position" DROP CONSTRAINT IF EXISTS trading_account_fk CASCADE;
ALTER TABLE serenity."position" ADD CONSTRAINT trading_account_fk FOREIGN KEY (trading_account_id)
REFERENCES serenity.trading_account (trading_account_id) MATCH FULL
ON DELETE SET NULL ON UPDATE CASCADE;
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.cash_instrument DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.cash_instrument ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: position_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.position_idx CASCADE;
CREATE UNIQUE INDEX position_idx ON serenity."position"
	USING btree
	(
	  position_date,
	  trading_account_id,
	  instrument_id
	);
-- ddl-end --

-- object: serenity.exchange_transfer_type | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_transfer_type CASCADE;
CREATE TABLE serenity.exchange_transfer_type (
	exchange_transfer_type_id smallint NOT NULL,
	exchange_transfer_type_code varchar(32) NOT NULL,
	CONSTRAINT exchange_transfer_type_pk PRIMARY KEY (exchange_transfer_type_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_transfer_type OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.exchange_transfer_type (exchange_transfer_type_id, exchange_transfer_type_code) VALUES (E'1', E'Deposit');
-- ddl-end --
INSERT INTO serenity.exchange_transfer_type (exchange_transfer_type_id, exchange_transfer_type_code) VALUES (E'2', E'Withdrawal');
-- ddl-end --

-- object: serenity.exchange_transfer_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_transfer_seq CASCADE;
CREATE SEQUENCE serenity.exchange_transfer_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_transfer_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.exchange_transfer | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_transfer CASCADE;
CREATE TABLE serenity.exchange_transfer (
	exchange_transfer_id integer NOT NULL DEFAULT nextval('serenity.exchange_transfer_seq'::regclass),
	exchange_id integer NOT NULL,
	exchange_transfer_method_id smallint NOT NULL,
	exchange_transfer_type_id smallint NOT NULL,
	currency_id integer NOT NULL,
	quantity decimal(24,16) NOT NULL,
	transfer_ref varchar(64) NOT NULL,
	cost_basis decimal(24,16),
	transfer_time timestamp NOT NULL,
	CONSTRAINT exchange_transfer_pk PRIMARY KEY (exchange_transfer_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_transfer OWNER TO postgres;
-- ddl-end --

-- object: currency_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_transfer DROP CONSTRAINT IF EXISTS currency_fk CASCADE;
ALTER TABLE serenity.exchange_transfer ADD CONSTRAINT currency_fk FOREIGN KEY (currency_id)
REFERENCES serenity.currency (currency_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_transfer_method | type: TABLE --
-- DROP TABLE IF EXISTS serenity.exchange_transfer_method CASCADE;
CREATE TABLE serenity.exchange_transfer_method (
	exchange_transfer_method_id smallint NOT NULL,
	exchange_transfer_method_code varchar(32) NOT NULL,
	CONSTRAINT exchange_transfer_method_pk PRIMARY KEY (exchange_transfer_method_id)

);
-- ddl-end --
-- ALTER TABLE serenity.exchange_transfer_method OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.exchange_transfer_method (exchange_transfer_method_id, exchange_transfer_method_code) VALUES (E'1', E'ACH');
-- ddl-end --
INSERT INTO serenity.exchange_transfer_method (exchange_transfer_method_id, exchange_transfer_method_code) VALUES (E'2', E'Blockchain');
-- ddl-end --

-- object: exchange_transfer_method_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_transfer DROP CONSTRAINT IF EXISTS exchange_transfer_method_fk CASCADE;
ALTER TABLE serenity.exchange_transfer ADD CONSTRAINT exchange_transfer_method_fk FOREIGN KEY (exchange_transfer_method_id)
REFERENCES serenity.exchange_transfer_method (exchange_transfer_method_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_transfer_method_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_transfer_method_code_idx CASCADE;
CREATE UNIQUE INDEX exchange_transfer_method_code_idx ON serenity.exchange_transfer_method
	USING btree
	(
	  exchange_transfer_method_code
	);
-- ddl-end --

-- object: exchange_transfer_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_transfer DROP CONSTRAINT IF EXISTS exchange_transfer_type_fk CASCADE;
ALTER TABLE serenity.exchange_transfer ADD CONSTRAINT exchange_transfer_type_fk FOREIGN KEY (exchange_transfer_type_id)
REFERENCES serenity.exchange_transfer_type (exchange_transfer_type_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: serenity.exchange_transfer_destination_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.exchange_transfer_destination_seq CASCADE;
CREATE SEQUENCE serenity.exchange_transfer_destination_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.exchange_transfer_destination_seq OWNER TO postgres;
-- ddl-end --

-- object: exchange_transfer_type_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_transfer_type_code_idx CASCADE;
CREATE UNIQUE INDEX exchange_transfer_type_code_idx ON serenity.exchange_transfer_type
	USING btree
	(
	  exchange_transfer_type_code
	);
-- ddl-end --

-- object: serenity.position_fill | type: TABLE --
-- DROP TABLE IF EXISTS serenity.position_fill CASCADE;
CREATE TABLE serenity.position_fill (
	position_id integer NOT NULL,
	fill_id integer NOT NULL
);
-- ddl-end --
-- ALTER TABLE serenity.position_fill OWNER TO postgres;
-- ddl-end --

-- object: position_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.position_fill DROP CONSTRAINT IF EXISTS position_fk CASCADE;
ALTER TABLE serenity.position_fill ADD CONSTRAINT position_fk FOREIGN KEY (position_id)
REFERENCES serenity."position" (position_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: fill_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.position_fill DROP CONSTRAINT IF EXISTS fill_fk CASCADE;
ALTER TABLE serenity.position_fill ADD CONSTRAINT fill_fk FOREIGN KEY (fill_id)
REFERENCES serenity.fill (fill_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: position_fill_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.position_fill DROP CONSTRAINT IF EXISTS position_fill_uq CASCADE;
ALTER TABLE serenity.position_fill ADD CONSTRAINT position_fill_uq UNIQUE (fill_id);
-- ddl-end --

-- object: serenity.mark_seq | type: SEQUENCE --
-- DROP SEQUENCE IF EXISTS serenity.mark_seq CASCADE;
CREATE SEQUENCE serenity.mark_seq
	INCREMENT BY 1
	MINVALUE 0
	MAXVALUE 2147483647
	START WITH 1
	CACHE 1
	NO CYCLE
	OWNED BY NONE;
-- ddl-end --
-- ALTER SEQUENCE serenity.mark_seq OWNER TO postgres;
-- ddl-end --

-- object: serenity.mark_type | type: TABLE --
-- DROP TABLE IF EXISTS serenity.mark_type CASCADE;
CREATE TABLE serenity.mark_type (
	mark_type_id smallint NOT NULL,
	mark_type_code varchar(32) NOT NULL,
	CONSTRAINT mark_type_pk PRIMARY KEY (mark_type_id)

);
-- ddl-end --
-- ALTER TABLE serenity.mark_type OWNER TO postgres;
-- ddl-end --

INSERT INTO serenity.mark_type (mark_type_id, mark_type_code) VALUES (E'1', E'YahooDailyClose');
-- ddl-end --

-- object: serenity.instrument_mark | type: TABLE --
-- DROP TABLE IF EXISTS serenity.instrument_mark CASCADE;
CREATE TABLE serenity.instrument_mark (
	mark_id integer NOT NULL DEFAULT nextval('serenity.mark_seq'::regclass),
	instrument_id integer NOT NULL,
	mark_type_id smallint NOT NULL,
	mark decimal(24,16) NOT NULL,
	mark_time timestamp NOT NULL,
	CONSTRAINT instrument_mark_pk PRIMARY KEY (mark_id)

);
-- ddl-end --
-- ALTER TABLE serenity.instrument_mark OWNER TO postgres;
-- ddl-end --

-- object: mark_type_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.instrument_mark DROP CONSTRAINT IF EXISTS mark_type_fk CASCADE;
ALTER TABLE serenity.instrument_mark ADD CONSTRAINT mark_type_fk FOREIGN KEY (mark_type_id)
REFERENCES serenity.mark_type (mark_type_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_instrument DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_instrument ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: currency_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.cash_instrument DROP CONSTRAINT IF EXISTS currency_fk CASCADE;
ALTER TABLE serenity.cash_instrument ADD CONSTRAINT currency_fk FOREIGN KEY (currency_id)
REFERENCES serenity.currency (currency_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: cash_instrument_uq | type: CONSTRAINT --
-- ALTER TABLE serenity.cash_instrument DROP CONSTRAINT IF EXISTS cash_instrument_uq CASCADE;
ALTER TABLE serenity.cash_instrument ADD CONSTRAINT cash_instrument_uq UNIQUE (currency_id);
-- ddl-end --

-- object: currency_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.currency_code_idx CASCADE;
CREATE UNIQUE INDEX currency_code_idx ON serenity.currency
	USING btree
	(
	  currency_code
	);
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_instrument DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.exchange_instrument ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_instrument_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_instrument_idx CASCADE;
CREATE UNIQUE INDEX exchange_instrument_idx ON serenity.exchange_instrument
	USING btree
	(
	  exchange_id,
	  exchange_instrument_code
	);
-- ddl-end --

-- object: instrument_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.instrument_mark DROP CONSTRAINT IF EXISTS instrument_fk CASCADE;
ALTER TABLE serenity.instrument_mark ADD CONSTRAINT instrument_fk FOREIGN KEY (instrument_id)
REFERENCES serenity.instrument (instrument_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: mark_code_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.mark_code_idx CASCADE;
CREATE UNIQUE INDEX mark_code_idx ON serenity.mark_type
	USING btree
	(
	  mark_type_code
	);
-- ddl-end --

-- object: mark_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.mark_idx CASCADE;
CREATE UNIQUE INDEX mark_idx ON serenity.instrument_mark
	USING btree
	(
	  mark_time,
	  instrument_id,
	  mark_type_id
	);
-- ddl-end --

-- object: instrument_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.instrument_idx CASCADE;
CREATE INDEX instrument_idx ON serenity.instrument_mark
	USING btree
	(
	  instrument_id
	);
-- ddl-end --

-- object: exchange_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.exchange_transfer DROP CONSTRAINT IF EXISTS exchange_fk CASCADE;
ALTER TABLE serenity.exchange_transfer ADD CONSTRAINT exchange_fk FOREIGN KEY (exchange_id)
REFERENCES serenity.exchange (exchange_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: exchange_transfer_ref_idx | type: INDEX --
-- DROP INDEX IF EXISTS serenity.exchange_transfer_ref_idx CASCADE;
CREATE UNIQUE INDEX exchange_transfer_ref_idx ON serenity.exchange_transfer
	USING btree
	(
	  transfer_ref,
	  exchange_id
	);
-- ddl-end --

-- object: parent_order_fk | type: CONSTRAINT --
-- ALTER TABLE serenity."order" DROP CONSTRAINT IF EXISTS parent_order_fk CASCADE;
ALTER TABLE serenity."order" ADD CONSTRAINT parent_order_fk FOREIGN KEY (parent_order_id)
REFERENCES serenity."order" (order_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: base_currency_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS base_currency_fk CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT base_currency_fk FOREIGN KEY (base_currency_id)
REFERENCES serenity.currency (currency_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --

-- object: quote_currency_fk | type: CONSTRAINT --
-- ALTER TABLE serenity.currency_pair DROP CONSTRAINT IF EXISTS quote_currency_fk CASCADE;
ALTER TABLE serenity.currency_pair ADD CONSTRAINT quote_currency_fk FOREIGN KEY (quote_currency_id)
REFERENCES serenity.currency (currency_id) MATCH FULL
ON DELETE RESTRICT ON UPDATE CASCADE;
-- ddl-end --


