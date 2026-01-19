import { formatRelative } from 'date-fns';

interface ArticleCardProps {
  title: string;
  summary: string;
  category: string;
  publishedAt: string;
}

export default function ArticleCard({
  title,
  summary,
  category,
  publishedAt,
}: ArticleCardProps) {
  return (
    <article className="group bg-card border border-border rounded-lg overflow-hidden shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1">
      <div className="h-48 bg-gradient-to-r from-primary/20 to-secondary/20 group-hover:from-primary/30 group-hover:to-secondary/30 transition-all duration-300" />
      <div className="p-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-primary bg-primary/10 px-2 py-1 rounded-md">
            {category}
          </span>
          <time className="text-sm text-muted-foreground">
            {formatRelative(new Date(publishedAt), new Date())}
          </time>
        </div>
        <h3 className="text-xl font-semibold mb-2 text-foreground group-hover:text-primary transition-colors">
          {title}
        </h3>
        <p className="text-muted-foreground line-clamp-2">{summary}</p>
        <button className="mt-4 text-sm font-medium text-primary hover:underline focus:outline-none focus:underline">
          Read more
        </button>
      </div>
    </article>
  );
}