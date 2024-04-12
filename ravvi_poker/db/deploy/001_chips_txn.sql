CREATE TYPE chips_txn_enum AS ENUM (
    'CHIPSIN',
    'CHIPSOUT',
    'MOVEIN',
    'MOVEOUT',
    'CASHIN',
    'CASHOUT',
    'RAKEBACK',
	'BUYIN',
	'REWARD'
);

CREATE TABLE chips_txn (
	id bigserial NOT NULL,
	created_ts timestamp without time zone DEFAULT now_utc() NOT NULL,
	created_by bigint NOT NULL,
	txn_type chips_txn_enum NOT NULL,
	txn_value numeric(20, 2) NOT NULL,
	club_id bigint NOT NULL,
	member_id bigint NULL,
	ref_member_id bigint NULL,
	ref_table_id bigint NULL,
	CONSTRAINT chips_txn_pk PRIMARY KEY (id)
);

ALTER TABLE chips_txn ADD CONSTRAINT chips_txn_club_fk FOREIGN KEY (club_id) REFERENCES club_profile(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE chips_txn ADD CONSTRAINT chips_txn_created_fk FOREIGN KEY (created_by) REFERENCES user_profile(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE chips_txn ADD CONSTRAINT chips_txn_trg_fk FOREIGN KEY (member_id) REFERENCES club_member(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE chips_txn ADD CONSTRAINT chips_txn_ref_fk FOREIGN KEY (member_id) REFERENCES club_member(id) ON DELETE RESTRICT ON UPDATE CASCADE;
CREATE INDEX chips_txn_club_id_idx ON chips_txn (club_id);

CREATE TABLE chips_club (
	id bigserial NOT NULL,
	txn_id bigint NOT NULL,
    club_id bigint NOT NULL,
    delta numeric(20, 2) NOT NULL,
    balance numeric(20, 2) NOT NULL,
	CONSTRAINT chips_club_pk PRIMARY KEY (id)
);

ALTER TABLE chips_club ADD CONSTRAINT chips_club_txn_fk FOREIGN KEY (txn_id) REFERENCES chips_txn(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE chips_club ADD CONSTRAINT chips_club_club_fk FOREIGN KEY (club_id) REFERENCES club_profile(id) ON DELETE RESTRICT ON UPDATE CASCADE;
CREATE UNIQUE INDEX chips_club_unq_idx ON chips_club (club_id,txn_id);

CREATE TABLE chips_agent (
	id bigserial NOT NULL,
	txn_id bigint NOT NULL,
    member_id bigint NOT NULL,
    delta numeric(20, 2) NOT NULL,
    balance numeric(20, 2) NOT NULL,
	CONSTRAINT chips_agent_pk PRIMARY KEY (id)
);

ALTER TABLE chips_agent ADD CONSTRAINT chips_agent_txn_fk FOREIGN KEY (txn_id) REFERENCES chips_txn(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE chips_agent ADD CONSTRAINT chips_agent_member_fk FOREIGN KEY (member_id) REFERENCES club_member(id) ON DELETE RESTRICT ON UPDATE CASCADE;
CREATE UNIQUE INDEX chips_agent_unq_idx ON chips_agent (member_id,txn_id);

CREATE TABLE chips_player (
	id bigserial NOT NULL,
	txn_id bigint NOT NULL,
    member_id bigint NOT NULL,
    delta numeric(20, 2) NOT NULL,
    balance numeric(20, 2) NOT NULL,
	CONSTRAINT chips_player_pk PRIMARY KEY (id)
);

ALTER TABLE chips_player ADD CONSTRAINT chips_player_txn_fk FOREIGN KEY (txn_id) REFERENCES chips_txn(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE chips_player ADD CONSTRAINT chips_player_member_fk FOREIGN KEY (member_id) REFERENCES club_member(id) ON DELETE RESTRICT ON UPDATE CASCADE;
CREATE UNIQUE INDEX chips_player_unq_idx ON chips_player (member_id,txn_id);
