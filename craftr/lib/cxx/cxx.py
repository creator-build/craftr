
import craftr
from nr import path

# TODO: Support precompiled headers.
# TODO: Support compiler-wrappers like ccache.
# TODO: Support linker-wrappers (eg. for coverage).

class CxxTargetHandler(craftr.TargetHandler):

  def __init__(self, toolchain=None):
    toolchain, fragment = (toolchain or options.toolchain).partition('#')[::2]
    self.toolchain = toolchain
    self.compiler = load('./impl/' + toolchain + '.py').get_compiler(fragment)

    print('Selected compiler: {} ({}) {} for {}'.format(
      self.compiler.name, self.compiler.id, self.compiler.version, self.compiler.arch))

  def init(self, context):
    props = context.target_properties
    # Largely inspired by the Qbs cpp module.
    # https://doc.qt.io/qbs/cpp-module.html

    # General
    # =======================

    # Specifies the target type. Either `executable` or `library`.
    props.add('cxx.type', craftr.String, 'executable')

    # The C and/or C++ input files for the target. If this property is not
    # set, the target will not be considered a C/C++ build target.
    props.add('cxx.srcs', craftr.StringList)

    # Allow the link-step to succeed even if symbols are unresolved.
    props.add('cxx.allowUnresolvedSymbols', craftr.Bool, False)

    # Combine C/C++ sources into a single translation unit. Note that
    # many projects can not be compiled in this fashion.
    props.add('cxx.combineCSources', craftr.Bool, False)
    props.add('cxx.combineCppSources', craftr.Bool, False)

    # Allow the linker to discard data that appears to be unused.
    # This value being undefined uses the linker's default.
    props.add('cxx.discardUnusedData', craftr.Bool)

    # Whether to store debug information in an external file or bundle
    # instead of within the binary. Defaults to True for MSVC, False
    # otherwise.
    props.add('cxx.separateDebugInformation', craftr.Bool)

    # Preprocessor definitions to set when compiling.
    props.add('cxx.defines', craftr.StringList)
    props.add('cxx.definesForStaticBuild', craftr.StringList)
    props.add('cxx.definesForSharedBuild', craftr.StringList)

    # Include search paths.
    props.add('cxx.includes', craftr.StringList)

    # Library search paths.
    props.add('cxx.libraryPaths', craftr.StringList)

    # Paths for the dynamic linker. This is only used when running
    # the product of a build target via Craftr.
    props.add('cxx.runPaths', craftr.StringList)

    # Dynamic libraries to link. You should use target dependencies
    # wherever possible rather than using this property.
    props.add('cxx.dynamicLibraries', craftr.StringList)

    # Static libraries to link. You should use target dependencies
    # wherever possible rather than using this property.
    props.add('cxx.staticLibraries', craftr.StringList)

    # List of files to automatically include at the beginning of
    # each translation unit.
    props.add('cxx.prefixHeaders', craftr.StringList)

    # Optimization level. Valid values are `none`, `size` and `speed`.
    props.add('cxx.optimization', craftr.String)

    # Whether to treat warnings as errors.
    props.add('cxx.treatWarningsAsErrors', craftr.Bool)

    # Specifies the warning level. Valid values are `none` or `all`.
    props.add('cxx.warningLevel', craftr.String)

    # Flags that are added to all compilation steps, independent of
    # the language.
    props.add('cxx.compilerFlags', craftr.StringList)

    # Specifies the way the library prefers to be linked. Either 'static' or 'dynamic'.
    props.add('cxx.preferredLinkage', craftr.String)

    # Flags that are added to C compilation.
    props.add('cxx.cFlags', craftr.String)

    # Flags that are added to C++ compilation.
    props.add('cxx.cppFlags', craftr.String)

    # The version of the C standard. If left undefined, the compiler's
    # default value is used. Valid values include `c89`, `c99` and `c11`.
    props.add('cxx.cStd', craftr.String)

    # The C standard library to link to.
    props.add('cxx.cStdlib', craftr.String)

    # The version of the C++ standard. If left undefined, the compiler's
    # default value is used. Valid values include `c++98`, `c++11`
    # and `c++14`.
    props.add('cxx.cppStd', craftr.String)

    # The C++ standard library to link to. Possible values are `libc++`
    # and `libstdc++`.
    props.add('cxx.cppStdlib', craftr.String)

    # Additional flags for the linker.
    props.add('cxx.linkerFlags', craftr.StringList)

    # Name of the entry point of an executable or dynamic library.
    props.add('cxx.entryPoint', craftr.String)

    # Type of the runtime library. Accepted values are `dynamic` and
    # `static`. Defaults to `dynamic` for MSVC, otherwise undefined.
    # For GCC/Clang, `static` will imply `-static-libc` or flags alike.
    props.add('cxx.runtimeLibrary', craftr.String)

    # Whether to enable exception handling.
    props.add('cxx.enableExceptions', craftr.Bool, True)

    # Whether to enable runtime type information
    props.add('cxx.enableRtti', craftr.Bool, True)

    # Apple Settings
    # =======================

    # Additional search paths for OSX frameworks.
    props.add('cxx.frameworkPaths', craftr.StringList)

    # OSX framework to link. If the framework is part of your project,
    # consider using a dependency instead.
    props.add('cxx.frameworks', craftr.StringList)

    # OSX framework to link weakly. If the framework is part of your project,
    # consider using a dependency instead.
    props.add('cxx.weakFrameworks', craftr.StringList)

    # A version number in the format [major] [minor] indicating the earliest
    # version that the product should run on.
    props.add('cxx.minimumMacosVersion', craftr.String)

    # Unix Settings
    # =======================

    # Generate position independent code. If this is undefined, PIC is
    # generated for libraries, but not applications.
    props.add('cxx.positionIndependentCode', craftr.Bool)

    # rpaths that are passed to the linker. Paths that also appear
    # in runPaths are ignored.
    props.add('cxx.rpaths', craftr.StringList)

    # The version to be appended to the soname in ELF shared libraries.
    props.add('cxx.soVersion', craftr.String)

    # Visibility level for exported symbols. Possible values include
    # `default`, `hidden`, `hiddenInlines` and `minimal (which combines
    # `hidden` and `hiddenInlines`).
    props.add('cxx.visibility', craftr.String)

    # Windows Settings
    # =======================

    # Whether to automatically generate a manifest file and include it in
    # the binary. Disable this property if you define your own .rc file.
    props.add('cxx.generateManifestFile', craftr.Bool, True)

    # Specifies the character set used in the Win32 API. Defaults to
    # "unicode".
    props.add('cxx.windowsApiCharacterSet', craftr.String)

    # Advanced Settings
    # =======================

    # TODO

    # Map of defines by language name.
    #props.add('cxx.definesByLanguage', 'Map[String, Map[String]]')

    # Map of defines by compiler ID.
    #props.add('cxx.definesByCompiler', 'Map[String, Map[String]]')

    # Map of defines by platform ID.
    #props.add('cxx.definesByPlatform', 'Map[String, Map[String]]')

    # Save temporary build prodcuts. Note that some toolchains (such as MSVC)
    # can not compile AND actually build at the same time.
    props.add('cxx.saveTemps', craftr.Bool, False)

    # Dependency Properties
    # =======================

    props = context.dependency_properties

    # If False, the dependency will not be linked, even if it is a valid
    # input for a linker rule. This property affects library dependencies only.
    props.add('cxx.link', craftr.Bool, True)


    self.compiler.init(context)

  def translate_target(self, target):
    context = target.context
    src_dir = target.directory
    build_dir = path.join(context.build_directory, target.module.name)

    data = target.get_props('cxx.', as_object=True)
    data.srcs = [path.canonical(x, src_dir) for x in target.get_prop_join('cxx.srcs')]
    data.includes = [path.canonical(x, src_dir) for x in target.get_prop_join('cxx.includes')]
    data.prefixHeaders = [path.canonical(x, src_dir) for x in target.get_prop_join('cxx.prefixHeaders')]


    # TODO: Determine whether we build an executable, static library
    #       or shared library.
    data.productFilename = target.name + '-' + target.module.version
    target.outputs.add(data.productFilename, ['exe'])

    c_srcs = []
    cpp_srcs = []
    for filename in data.srcs:
      if filename.endswith('.c'): c_srcs.append(filename)
      if filename.endswith('.cpp') or filename.endswith('.cc'):
        cpp_srcs.append(filename)

    compile_actions = []
    obj_files = []
    for (srcs, lang) in ((c_srcs, 'c'), (cpp_srcs, 'cpp')):
      if not srcs: continue
      command = self.compiler.build_compile_flags(lang, target, data)
      action = target.add_action('cxx.compile' + lang.capitalize(),
        environ=self.compiler.compiler_env, commands=[command], input=True)
      for src in srcs:
        build = action.add_buildset()
        build.files.add(src, ['in', 'src', 'src.' + lang])
        self.compiler.update_compile_buildset(build, target, data)
        obj_files += build.files.tagged('out,obj')
      compile_actions.append(action)

    link_action = None
    if obj_files:
      command = self.compiler.build_link_flags('cpp' if cpp_srcs else 'c', target, data)
      link_action = target.add_action('cxx.link', commands=[command],
        environ=self.compiler.linker_env, deps=compile_actions)
      build = link_action.add_buildset()
      build.files.add(obj_files, ['in', 'obj'])
      build.files.add(data.productFilename, ['out', 'product'])
      self.compiler.update_link_buildset(build, target, data)

    if link_action and data.type == 'executable':
      command = [data.productFilename]
      action = target.add_action('cxx.run', commands=[command],
        explicit=True, syncio=True, output=False)
      action.add_buildset()


context.register_handler(CxxTargetHandler())
