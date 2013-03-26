ALTER TABLE wikipbxweb_endpoint ADD COLUMN userprofile_id integer;

ALTER TABLE wikipbxweb_endpoint ADD CONSTRAINT valid_userprofile_id FOREIGN KEY (userprofile_id) REFERENCES wikipbxweb_userprofile (user_id) INITIALLY DEFERRED;
ALTER TABLE wikipbxweb_extension ADD COLUMN endpoint_id integer;

ALTER TABLE wikipbxweb_extension ADD CONSTRAINT valid_endpoint_id FOREIGN KEY (endpoint_id) REFERENCES wikipbxweb_endpoint (id) INITIALLY DEFERRED;