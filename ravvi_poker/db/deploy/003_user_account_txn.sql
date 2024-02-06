ALTER TABLE ONLY user_account_txn ADD COLUMN total_balance numeric(20,4) DEFAULT 0.0;
ALTER TABLE ONLY user_account_txn ADD COLUMN sender_id int DEFAULT null;