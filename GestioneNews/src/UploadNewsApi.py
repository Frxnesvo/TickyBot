from pygooglenews import GoogleNews
import boto3

TOPICS = ['NATION', 'BUSINESS', 'SPORTS', 'TECHNOLOGY', 'ENTERTAINMENT']

class UploadNewsApi:
    def __init__(self):
        dynamo= boto3.resource('dynamodb')
        self.table= dynamo.Table('News')

    def getNews(self):
        googleNews = GoogleNews(lang='it', country='IT')
        return [self.__takeFirstNewsByTopic(googleNews, topic) for topic in TOPICS]

    def getActiveChannelsIds(self):
        # Definisco il filtro di espressione per selezionare solo le tuple dove stato è 'attiva'
        filter_expression = 'stato = :stato_val'
        expression_attribute_values = {':stato_val': 'attiva'}

        response = self.table.scan(
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        return [(item['channelid'], item['community']) for item in response['Items']]


    def __takeFirstNewsByTopic(self, googleNews, topic):
        news = googleNews.topic_headlines(topic)
        return news['entries'][0]