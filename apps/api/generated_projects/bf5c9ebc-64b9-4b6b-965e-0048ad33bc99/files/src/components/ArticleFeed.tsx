import ArticleCard from './ArticleCard';

export default function ArticleFeed() {
  const articles = [
    {
      id: 1,
      title: 'New Exoplanet Discovered in Habitable Zone',
      summary:
        'Astronomers using AI algorithms detect a potentially habitable exoplanet 12 light-years away.',
      category: 'Space',
      publishedAt: '2023-10-05T14:30:00Z',
    },
    {
      id: 2,
      title: 'SpaceX Launches New Satellite Array',
      summary:
        'Latest batch of Starlink satellites deployed to enhance global internet coverage.',
      category: 'Tech',
      publishedAt: '2023-10-04T09:15:00Z',
    },
    {
      id: 3,
      title: 'NASA Prepares for Artemis II Mission',
      summary:
        'Crew training underway for the first crewed mission to the Moon in over 50 years.',
      category: 'Space',
      publishedAt: '2023-10-03T18:45:00Z',
    },
    {
      id: 4,
      title: 'AI Ethics in Space Exploration',
      summary:
        'Debate grows over the role of AI in autonomous space missions and decision-making.',
      category: 'Tech',
      publishedAt: '2023-10-02T11:20:00Z',
    },
  ];

  return (
    <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" aria-labelledby="news-feed-heading">
      <h2 id="news-feed-heading" className="sr-only">Latest News Articles</h2>
      {articles.map((article) => (
        <ArticleCard
          key={article.id}
          title={article.title}
          summary={article.summary}
          category={article.category}
          publishedAt={article.publishedAt}
        />
      ))}
    </section>
  );
}