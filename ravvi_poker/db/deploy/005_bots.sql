UPDATE user_profile 
SET username=CONCAT('Bot-',id)
WHERE id>0 and id<100;
