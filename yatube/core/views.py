from django.shortcuts import render


def page_not_found(request, exception):
    """Функция для страницы 404. Страницы не существует."""
    return render(
        request, 'core/404.html',
        {'path': request.path},
        status=404
    )


def csrf_failure(request, reason=''):
    """Функция для страницы 403. Ошибка доступа."""
    return render(request, 'core/403csrf.html')


def server_error(request):
    return render(request, 'core/500.html', status=500)
