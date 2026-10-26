
CREATE TABLE inventory.batch_reservation_allocations (
	id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	reservation_id UUID NOT NULL, 
	batch_id UUID NOT NULL, 
	quantity NUMERIC(20, 4) NOT NULL, 
	status TEXT NOT NULL, 
	CONSTRAINT pk_batch_reservation_allocations PRIMARY KEY (id), 
	CONSTRAINT uq_batch_reservation_allocations_reservation_id UNIQUE (reservation_id, batch_id), 
	CONSTRAINT ck_batch_reservation_allocations_rule_0 CHECK (quantity > 0), 
	CONSTRAINT fk_batch_reservation_allocations_reservation_id_stock_r_e655 FOREIGN KEY(reservation_id) REFERENCES inventory.stock_reservations (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_batch_reservation_allocations_batch_id_stock_batches FOREIGN KEY(batch_id) REFERENCES inventory.stock_batches (id) ON DELETE RESTRICT
)

