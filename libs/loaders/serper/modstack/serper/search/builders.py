from typing import Any

from modstack.serper.search import SerperKnowledgeGraph, SerperOrganicResult, SerperPeopleAlsoAsk, SerperSearchResponse

def build_search_response(data: Any) -> SerperSearchResponse:
    return SerperSearchResponse(
        organic=_build_organic_results(data['organic']),
        knowledge_graph=_build_search_knowledge_graph(data['knowledgeGraph']) if 'knowledgeGraph' in data else None,
        people_also_ask=_build_people_also_ask(data['peopleAlsoAsk']) if 'peopleAlsoAsk' in data else None,
        related_searches=_build_related_searches(data['relatedSearches']) if 'relatedSearches' in data else None
    )

def _build_organic_results(data: list[Any]) -> list[SerperOrganicResult]:
    return [
        SerperOrganicResult(
            title=result['title'],
            link=result['link'],
            snippet=result['snippet'],
            position=result['position'],
            date=result['date'],
            image_url=result['imageUrl'],
            site_links=result['sitelinks'],
            attributes=result['attributes']
        )
        for result in data
    ]

def _build_search_knowledge_graph(data: Any) -> SerperKnowledgeGraph:
    return SerperKnowledgeGraph(
        title=data['title'],
        type=data['type'],
        website=data['website'],
        image_url=data['imageUrl'],
        description=data['description'],
        description_source=data['descriptionSource'],
        description_link=data['descriptionLink'],
        attributes=data['attributes']
    )

def _build_people_also_ask(data: list[Any]) -> list[SerperPeopleAlsoAsk]:
    return [
        SerperPeopleAlsoAsk(
            question=result['question'],
            title=result['title'],
            snippet=result['snippet'],
            link=result['link']
        )
        for result in data
    ]

def _build_related_searches(data: list[Any]) -> list[str]:
    return [result['query'] for result in data]