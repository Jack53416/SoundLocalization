// 
module.exports = function(grunt) {
  grunt.initConfig({
    ts: {
      default: {
        tsconfig: './tsconfig.json'
        }
      },
      browserify: {
          default: {
              src: ['dist/public/js/main.js'],
              dest: 'dist/public/js/main_brows.js'
          }
      },
	eslint: {
		options: {
			configFile: '.eslintrc.yml'
		},
		target: 'src/*.ts'
	},
	watch: {
		scripts: {
		files: ['src/*.ts'],
		tasks: ['ts', 'eslint'],
		options: {
		  spawn: false
		}
  }
}
  });
    grunt.loadNpmTasks("grunt-ts");
    grunt.loadNpmTasks("grunt-eslint");
    grunt.loadNpmTasks('grunt-contrib-watch');
    grunt.loadNpmTasks('grunt-browserify');

    grunt.registerTask("default", ["watch"]);
    grunt.registerTask('lint', ['eslint']);
    grunt.registerTask('build', ['ts', 'browserify']);
};