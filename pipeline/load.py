import boto3


def load_data(data: dict) -> None:
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('c25-gabi-db')

    for item in data:
        table.put_item(
            Item={
                'PrimaryKey': f"{item['id']}",
                'SortKey': f"{item['publication_time']}",
                'Outlet': f"{item['outlet']}",
                'Title': f"{item['title']}",
                'Content': f"{item['content']}",
                'Author': f"{item['author']}",
                'Keywords': f"{item['keywords']}",
                'Individuals': f"{item['individuals']}",
                'Companies': f"{item['companies']}",
                'Sentiment': f"{item['sentiment']}"
            }
        )
