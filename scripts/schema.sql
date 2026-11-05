USE epic_events;

CREATE TABLE `role` (
	id_role INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id_role), 
	UNIQUE (name)
);

CREATE TABLE employee (
	id_employee INTEGER NOT NULL AUTO_INCREMENT, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(250) NOT NULL, 
	password_hash VARCHAR(250) NOT NULL, 
	is_active BOOL NOT NULL DEFAULT 1, 
	id_role INTEGER NOT NULL, 
	PRIMARY KEY (id_employee), 
	UNIQUE (email), 
	FOREIGN KEY(id_role) REFERENCES `role` (id_role) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE customer (
	id_customer INTEGER NOT NULL AUTO_INCREMENT, 
	full_name VARCHAR(100) NOT NULL, 
	email VARCHAR(250) NOT NULL, 
	phone_number VARCHAR(20) NOT NULL, 
	company VARCHAR(250), 
	creation_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	last_update_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, 
	is_active BOOL NOT NULL DEFAULT 1, 
	id_sales_employee INTEGER NOT NULL, 
	PRIMARY KEY (id_customer), 
	UNIQUE (email), 
	FOREIGN KEY(id_sales_employee) REFERENCES employee (id_employee) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE contract (
	id_contract INTEGER NOT NULL AUTO_INCREMENT, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	outstanding_balance NUMERIC(12, 2) NOT NULL, 
	creation_datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	is_signed BOOL NOT NULL DEFAULT 0, 
	id_customer INTEGER NOT NULL, 
	PRIMARY KEY (id_contract), 
	CONSTRAINT ck_contract_total_amount_nonnegative CHECK (total_amount >= 0), 
	CONSTRAINT ck_contract_outstanding_balance_nonnegative CHECK (outstanding_balance >= 0), 
	CONSTRAINT ck_contract_outstanding_balance_equal_or_less_than_total_amount CHECK (outstanding_balance <= total_amount), 
	CONSTRAINT ck_contract_is_signed_boolean CHECK (is_signed IN (0, 1)), 
	FOREIGN KEY(id_customer) REFERENCES customer (id_customer) ON DELETE RESTRICT ON UPDATE CASCADE
);

CREATE TABLE event (
	id_event INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(250) NOT NULL, 
	start_datetime DATETIME NOT NULL, 
	end_datetime DATETIME NOT NULL, 
	location VARCHAR(250) NOT NULL, 
	attendees_count INTEGER NOT NULL, 
	notes TEXT, 
	id_contract INTEGER NOT NULL, 
	id_support_employee INTEGER, 
	PRIMARY KEY (id_event), 
	CONSTRAINT ck_event_end_datetime_later_than_start_datetime CHECK (end_datetime > start_datetime), 
	CONSTRAINT ck_event_attendees_count_more_than_zero CHECK (attendees_count > 0), 
	FOREIGN KEY(id_contract) REFERENCES contract (id_contract) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_support_employee) REFERENCES employee (id_employee) ON DELETE RESTRICT ON UPDATE CASCADE
);
