-- Add error_message column if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='repositories' 
        AND column_name='error_message'
    ) THEN
        ALTER TABLE repositories 
        ADD COLUMN error_message TEXT;
    END IF;
END $$; 