ALTER TABLE wikipbxweb_endpoint drop COLUMN mailbox;
ALTER TABLE wikipbxweb_endpoint drop COLUMN vm_password;

ALTER TABLE wikipbxweb_userprofile ADD COLUMN mailbox varchar(40);
ALTER TABLE wikipbxweb_userprofile ADD COLUMN vm_password varchar(100);

