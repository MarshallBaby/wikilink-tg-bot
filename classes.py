class Statement:
        
    def check(self, message):
        global connection
        global pizza
        print(pizza)
        chat_id = message.chat.id
        connection.commit()
        sql = "SELECT `statement` FROM `temp` WHERE `id` = " + str(chat_id)
        cursor.execute(sql)
        res = cursor.fetchone()[0]
        return res