
--Recursive Query: Track Borrowing Chains for a Book

--Track the borrowing history of a specific book (BookID), showing a chain of borrowers who checked out the book sequentially.


WITH RECURSIVE Borrowing_Chain AS (
    -- Base Case: Get all borrowers of the book
    SELECT 
        b.Username, 
        c.First_Name, 
        c.Last_Name, 
        b.BookID, 
        b.Date_Out, 
        b.Due_Date, 
        b.Penalty,
        1 AS Chain_Level
    FROM Borrows b
    JOIN Customer c ON b.Username = c.Username
    WHERE b.BookID = '0000000002431#001'

    UNION ALL

    -- Recursive Case: Find the next borrower after the previous one returned the book
    SELECT 
        next_borrower.Username, 
        c.First_Name, 
        c.Last_Name, 
        next_borrower.BookID, 
        next_borrower.Date_Out, 
        next_borrower.Due_Date, 
        next_borrower.Penalty,
        bc.Chain_Level + 1
    FROM Borrows next_borrower
    JOIN Borrowing_Chain bc 
        ON next_borrower.BookID = bc.BookID 
        AND next_borrower.Date_Out > bc.Due_Date
    JOIN Customer c ON next_borrower.Username = c.Username
)
SELECT 
    Username, 
    First_Name, 
    Last_Name, 
    BookID, 
    Date_Out, 
    Due_Date, 
    Penalty, 
    Chain_Level
FROM Borrowing_Chain
ORDER BY Chain_Level, Date_Out;



--Explanation:
--Base Case:
--The query starts with the first borrower of the book (BookID). 
--It fetches the borrower's information along with the borrowing date (Date_Out) and due date (Due_Date).
--The LIMIT 1 ensures it starts with the first recorded borrower of the book.
--Recursive Case:
--The query then recursively finds subsequent borrowers who checked out the same book after it was returned.
--It uses the condition next_borrower.Date_Out > bc.Due_Date to find borrowers who checked out the book after it was previously due.
--Final Output:
--The recursive query builds a chain of borrowers, showing who borrowed the book, when they borrowed it, and if any penalties were incurred.
--The chain level (Chain_Level) shows the sequence in which the book was borrowed.

--Importance:
--This query is helpful for analyzing book demand and circulation within the library.
--It helps the library identify popular books that may need more copies due to high demand.

Usage:
SELECT * FROM Borrowing_Chain;



--SECURITY MECHANISM 1: User Roles and Permissions
-- Creating roles
CREATE ROLE Librariann;
CREATE ROLE Managerr;
CREATE ROLE Customerr;

-- Granting permissions to Librarian
GRANT SELECT, INSERT, UPDATE ON Borrows TO Librariann;
GRANT SELECT ON Customer, Stores_Items, Stores_Booksforsale TO Librariann;

-- Granting full access to Admin
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO Managerr;

-- Granting read-only access to Customers
GRANT SELECT ON Books_for_Sale, Books_for_Rent TO Customerr;




--SECURITY MECHANISM 2: Restrict data access based on the user’s role or identity
-- Enable row-level security on the Borrows table
ALTER TABLE Borrows ENABLE ROW LEVEL SECURITY;

-- Create a policy to allow only the borrower to see their records
CREATE POLICY Borrower_Policy
ON Borrows
USING (Username = CURRENT_USER);

-- Apply the policy
ALTER TABLE Borrows FORCE ROW LEVEL SECURITY;



--SECURITY MECHANISM 3: SQL INJECTION

--SQLL INJECTION IS WHEN TRYING TO INSERT:
--SELECT * FROM Customer WHERE Username = 'en01' OR '1'='1';

--QUERY:
PREPARE find_customer (VARCHAR) AS
SELECT * FROM Customer WHERE Username = $1;
EXECUTE find_customer('en01');


--Security Mechanism 4: Encryption and Decryption

CREATE EXTENSION pgcrypto;
ALTER TABLE Authentication_System DROP CONSTRAINT chk_passcode;
ALTER TABLE Authentication_System
ALTER COLUMN Passcode TYPE BYTEA USING pgp_sym_encrypt(Passcode::TEXT, 's3cUr3!kEy#2023@P0stgreSQL^');


--Encryption:
Insert into Authentication_System Values('myh17@gmail.com',pgp_sym_encrypt('Qwerty123#@', 's3cUr3!kEy#2023@P0stgreSQL^'));

--Decryption:
SELECT Email,
       pgp_sym_decrypt(Passcode, 's3cUr3!kEy#2023@P0stgreSQL^') AS Decrypted_Passcode
FROM Authentication_System
WHERE Email = 'myh17@gmail.com';










