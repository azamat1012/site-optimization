from django.shortcuts import render
from django.db.models import Count, Prefetch
from blog.models import Comment, Post, Tag


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count if hasattr(post, 'comments_count') else 0,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title if post.tags.exists() else None,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def index(request):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    most_popular_posts = Post.objects.popular().prefetch_related(
        Prefetch('tags', queryset=tags_with_counts),
        'author'
    )[:5].fetch_with_comments_count()

    most_fresh_posts = Post.objects.order_by('-published_at').prefetch_related(
        Prefetch('tags', queryset=tags_with_counts),
        'author'
    )[:5]

    most_popular_tags = tags_with_counts.order_by('-posts_count')[:5]

    context = {
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    post = Post.objects.prefetch_related(
        Prefetch('tags', queryset=tags_with_counts),
        Prefetch('comments', queryset=Comment.objects.select_related('author')),
        'author'
    ).annotate(
        likes_count=Count('likes'),
        comments_count=Count('comments')
    ).get(slug=slug)
    serialized_comments = [
        {
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        }
        for comment in post.comments.all()
    ]
    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
    }

    most_popular_tags = tags_with_counts.order_by('-posts_count')[:5]
    most_popular_posts = Post.objects.popular().prefetch_related(
        Prefetch('tags', queryset=tags_with_counts),
        'author'
    )[:5].fetch_with_comments_count()

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))
    tag = Tag.objects.get(title=tag_title)
    most_popular_tags = tags_with_counts.order_by('-posts_count')[:5]
    most_popular_posts = Post.objects.popular().prefetch_related(
        Prefetch('tags', queryset=tags_with_counts),
        'author'
    )[:5].fetch_with_comments_count()

    related_posts = tag.posts.prefetch_related(
        Prefetch('tags', queryset=tags_with_counts),
        'author'
    )[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    return render(request, 'contacts.html', {})
