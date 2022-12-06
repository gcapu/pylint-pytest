import inspect
import astroid


def _is_pytest_mark_usefixtures(decorator):
    # expecting @pytest.mark.usefixture(...)
    try:
        if isinstance(decorator, astroid.Call) and \
                decorator.func.attrname == 'usefixtures' and \
                decorator.func.expr.attrname == 'mark' and \
                decorator.func.expr.expr.name == 'pytest':
            return True
    except AttributeError:
        pass
    return False


def _is_pytest_mark(decorator):
    try:
        deco = decorator  # as attribute `@pytest.mark.trylast`
        if isinstance(decorator, astroid.Call):
            deco = decorator.func  # as function `@pytest.mark.skipif(...)`
        if deco.expr.attrname == 'mark' and deco.expr.expr.name == 'pytest':
            return True
    except AttributeError:
        pass
    return False


def _is_pytest_fixture(decorator, fixture=True, yield_fixture=True):
    attr = None
    to_check = set()

    if fixture:
        to_check.add('fixture')

    if yield_fixture:
        to_check.add('yield_fixture')

    try:
        if isinstance(decorator, astroid.Attribute):
            # expecting @pytest.fixture
            attr = decorator

        if isinstance(decorator, astroid.Call):
            # expecting @pytest.fixture(scope=...)
            attr = decorator.func

        if attr and attr.attrname in to_check \
                and attr.expr.name == 'pytest':
            return True
    except AttributeError:
        pass

    return False



def _is_pytest_fixture(decorator, fixture=True, yield_fixture=True):
    to_check = set()

    if fixture:
        to_check.add('fixture')

    if yield_fixture:
        to_check.add('yield_fixture')

    def _check_attribute(attr):
        """
        handle astroid.Attribute, i.e., when the fixture function is
        used by importing the pytest module
        """
        return attr.attrname in to_check and attr.expr.name == 'pytest'

    def _check_name(name_):
        """
        handle astroid.Name, i.e., when the fixture function is
        directly imported
        """
        function_name = decorator.name
        module_name = decorator.root().globals[function_name][0].modname
        return function_name in to_check and module_name == 'pytest'

    try:
        if isinstance(decorator, astroid.Name):
            # expecting @fixture
            return _check_name(decorator)
        if isinstance(decorator, astroid.Attribute):
            # expecting @pytest.fixture
            return _check_attribute(decorator)
        if isinstance(decorator, astroid.Call):
            func = decorator.func
            if isinstance(func, astroid.Name):
                # expecting @fixture(scope=...)
                return _check_name(func)
            else:
                # expecting @pytest.fixture(scope=...)
                return _check_attribute(func)

    except AttributeError:
        pass

    return False


def _can_use_fixture(function):
    if isinstance(function, astroid.FunctionDef):

        # test_*, *_test
        if function.name.startswith('test_') or function.name.endswith('_test'):
            return True

        if function.decorators:
            for decorator in function.decorators.nodes:
                # usefixture
                if _is_pytest_mark_usefixtures(decorator):
                    return True

                # fixture
                if _is_pytest_fixture(decorator):
                    return True

    return False


def _is_same_module(fixtures, import_node, fixture_name):
    '''Comparing pytest fixture node with astroid.ImportFrom'''
    try:
        for fixture in fixtures[fixture_name]:
            for import_from in import_node.root().globals[fixture_name]:
                if inspect.getmodule(fixture.func).__file__ == \
                        import_from.parent.import_module(import_from.modname,
                                                         False,
                                                         import_from.level).file:
                    return True
    except:  # pylint: disable=bare-except
        pass
    return False
