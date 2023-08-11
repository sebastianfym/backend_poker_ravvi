ALTER TABLE poker_table
ADD COLUMN game_subtype varchar(100) default null,
ADD COLUMN table_seats smallint default null;
