from picura.core.context_processors import picura_context


def test_picura_context_returns_version():
    context = picura_context(None)
    assert 'picura_version' in context
    assert isinstance(context['picura_version'], str)
    assert context['picura_version']
