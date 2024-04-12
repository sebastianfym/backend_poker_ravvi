CREATE OR REPLACE VIEW club_member_view
AS
SELECT 
m.*, 
u.name,
u.image_id,
u.country 
FROM club_member m
join user_profile u on u.id=m.user_id;
